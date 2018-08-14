import sys
sys.path.append('.')

from atlas import *

@Module
def UartReceiver(clock_rate, baud_rate, fifo_depth):
    io = Io({
        'uart_rx': Input(Bits(1)),
        'dequeue': Input(Bits(1)),
        'dequeue_data': Output(Bits(8)),
        'data_available': Output(Bits(1))
    })

    clocks_per_bit = clock_rate // baud_rate
    clocks_per_half_bit = clocks_per_bit // 2

    states = Enum(['idle', 'start', 'read', 'stop'])
    state = Reg(Bits(states.bitwidth), reset_value=states.idle)

    fifo_bits = 1 if fifo_depth == 1 else Log2Ceil(fifo_depth)

    data_reg = Reg([Bits(1) for _ in range(8)])
    fifo_ram = Reg([Bits(8) for _ in range(fifo_depth)])
    enq_addr = Reg(Bits(fifo_bits), reset_value=0)
    deq_addr = Reg(Bits(fifo_bits), reset_value=0)
    enqueue = Wire(Bits(1))

    enqueue <<= 0
    enqueue_data = Cat([data_reg[8 - i - 1] for i in range(8)])

    clock_counter = Reg(Bits(32), reset_value=0)
    bit_counter = Reg(Bits(4), reset_value=0)

    clock_counter <<= clock_counter + 1
    io.data_available <<= (enq_addr != deq_addr)
    io.dequeue_data <<= fifo_ram[deq_addr]

    with enqueue:
        fifo_ram[enq_addr] <<= enqueue_data
        enq_addr <<= enq_addr + 1

    with io.dequeue & (enq_addr != deq_addr):
        deq_addr <<= deq_addr + 1

    with state == states.idle:
        clock_counter <<= 0
        with ~io.uart_rx:
            state <<= states.start

    with state == states.start:
        with io.uart_rx & (clock_counter < clocks_per_half_bit):
            state <<= states.idle

        with clock_counter >= clocks_per_bit:
            state <<= states.read
            clock_counter <<= 0
            bit_counter <<= 0

            for i in range(8):
                data_reg[i] <<= 0

    with state == states.read:
        with clock_counter == clocks_per_half_bit:
            data_reg[bit_counter] <<= io.uart_rx

        with clock_counter == clocks_per_bit:
            clock_counter <<= 0

            with bit_counter == 7:
                state <<= states.stop

            with otherwise:
                bit_counter <<= bit_counter + 1

    with state == states.stop:
        with clock_counter == clocks_per_bit:
            state <<= states.idle
            enqueue <<= 1

    NameSignals(locals())

@Module
def UartTransmitter(clock_rate, baud_rate, fifo_depth):
    io = Io({
        'uart_tx': Output(Bits(1)),
        'enqueue': Input(Bits(1)),
        'enqueue_data': Input(Bits(8)),
        'ready': Output(Bits(1))
    })

    clocks_per_bit = clock_rate // baud_rate

    states = Enum(['idle', 'start', 'write', 'stop'])
    state = Reg(Bits(states.bitwidth), reset_value=states.idle)

    tx_buf = Reg([Bits(1) for _ in range(8)])

    clock_counter = Reg(Bits(32), reset_value=0)
    bit_counter = Reg(Bits(4), reset_value=0)

    data_reg = Reg(Bits(8), reset_value=0)

    fifo_ram = Reg([Bits(8) for _ in range(fifo_depth)])
    enq_addr = Reg(Bits(Log2Ceil(fifo_depth)), reset_value=0)
    deq_addr = Reg(Bits(Log2Ceil(fifo_depth)), reset_value=0)
    enqueue = Wire(Bits(1))

    enqueue <<= 0

    data_count = Reg(Bits(fifo_depth + 1), reset_value=0)
    full = Wire(Bits(1))
    empty = Wire(Bits(1))

    dequeue = Wire(Bits(1))
    dequeue <<= 0

    dequeue_data = Wire(Bits(8))

    full <<= data_count >= fifo_depth
    empty <<= data_count == 0
    dequeue_data <<= fifo_ram[deq_addr]
    io.ready <<= ~full | dequeue

    with ~enqueue & dequeue:
        with ~empty:
            data_count <<= data_count - 1
            deq_addr <<= deq_addr + 1

    with enqueue & ~dequeue:
        with ~full:
            data_count <<= data_count + 1
            enq_addr <<= enq_addr + 1
            fifo_ram[enq_addr] <<= io.enqueue_data

    with enqueue & dequeue:
        deq_addr <<= deq_addr + 1
        enq_addr <<= enq_addr + 1
        fifo_ram[enq_addr] <<= io.enqueue_data

    with dequeue:
        for i in range(8):
            tx_buf[i] <<= dequeue_data(i, i)

    io.uart_tx <<= 1
    clock_counter <<= clock_counter + 1

    with state == states.idle:
        clock_counter <<= 0
        bit_counter <<= 0

        with ~empty:
            dequeue <<= 1
            state <<= states.start

    with state == states.start:
        io.uart_tx <<= 0
        with clock_counter > clocks_per_bit:
            state <<= states.write


    with state == states.write:
        io.uart_tx <<= tx_buf[bit_counter]

        with clock_counter > clocks_per_bit:
            with bit_counter == 7:
                state <<= states.stop
            with otherwise:
                bit_counter <<= bit_counter + 1

    with state == states.stop:
        with clock_counter > clocks_per_bit:
            state <<= states.idle

    NameSignals(locals())


circuit = Circuit(True, True)
with circuit:
    # top = UartReceiver(50000000, 115200, 8)
    top = UartTransmitter(50000000, 115200, 8)

circuit.SetTop(top)

EmitCircuit(circuit, 'test/uart.v')
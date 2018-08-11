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
    state = Reg(Bits(states.bitwidth))

    state.reset = states.idle

    fifo_bits = 1 if fifo_depth == 1 else Log2Ceil(fifo_depth)

    true = Const(1)
    false = Const(0)

    data_reg = Reg(Bits(8), reset_value=Const(0, 8))
    fifo_ram = Reg([Bits(8) for _ in range(fifo_depth)])
    enq_addr = Reg(Bits(fifo_bits), reset_value=Const(0, fifo_bits))
    deq_addr = Reg(Bits(fifo_bits), reset_value=Const(0, fifo_bits))
    enqueue = Wire(Bits(1))

    enqueue <<= false

    data_reg = Reg(Bits(1, (8,)))

    clock_counter = Reg(Bits(32), reset_value=Const(0, 32))
    bit_counter = Reg(Bits(4), reset_value=Const(0, 4))

    clock_counter <<= clock_counter + Const(1, clock_counter.width)
    io.data_available <<= (enq_addr != deq_addr)
    io.dequeue_data <<= fifo_ram[deq_addr]

    with enqueue:
        fifo_ram[enq_addr] <<= data_reg
        enq_addr <<= enq_addr + Const(1, enq_addr.width)

    with io.dequeue & (enq_addr != deq_addr):
        deq_addr <<= deq_addr + Const(1, enq_addr.width)


    # TODO: Make a switch construct

    with state == states.idle:
        clock_counter <<= Const(0, clock_counter.width)
        with ~io.uart_rx:
            state <<= states.start

    with state == states.start:
        with io.uart_rx & (clock_counter < Const(clocks_per_half_bit, clock_counter.width)):
            state <<= states.idle

        with clock_counter >= Const(clocks_per_bit, clock_counter.width):
            state <<= states.read
            clock_counter <<= Const(0, clock_counter.width)
            bit_counter <<= Const(0, bit_counter.width)

            for i in range(8):
                data_reg[i] <<= false

    with state == states.read:
        with clock_counter == clocks_per_half_bit:
            data_reg[bit_counter] <<= io.uart_rx

        with clock_counter == clocks_per_bit:
            clock_counter <<= Const(0, clock_counter.width)

            with bit_counter == Const(7, bit_counter.width):
                state <<= states.stop

            with otherwise:
                bit_counter <<= bit_counter + Const(1, bit_counter.width)

    with state == states.stop:
        with clock_counter == Const(clocks_per_bit, clock_counter.width):
            state <<= states.idle
            enqueue <<= true

    NameSignals(locals())



circuit = Circuit(True, True)
with circuit:
    top = UartReceiver(50000000, 115200, 8)

circuit.SetTop(top)

EmitCircuit(circuit, 'test/uart.v')
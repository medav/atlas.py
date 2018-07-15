import sys
sys.path.append('.')

import atlas.firrtl.emitter as emitter
from atlas.frontend import *

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

    data_reg = RegInit(Bits(8), Const(0))
    fifo_ram = Reg(Bits(8, (fifo_depth,)))
    enq_addr = RegInit(Bits(Log2Ceil(fifo_depth)), Const(0))
    deq_addr = RegInit(Bits(Log2Ceil(fifo_depth)), Const(0))
    enqueue = WireInit(Bits(1), F)

    data_reg = Reg(Bits(1, (8,)))
    # TODO: Add mechanism to allow initial values that are array types

    clock_counter = RegInit(Bits(32), Const(0))
    bit_counter = RegInit(Bits(4), Const(0))

    clock_counter <<= clock_counter + Const(1)
    io.data_available <<= (enq_addr != deq_addr)
    io.dequeue_data <<= fifo_ram[deq_addr]

    with enqueue:
        fifo_ram[enq_addr] <<= data_reg
        enq_addr <<= enq_addr + Const(1)

    with io.dequeue & (enq_addr != deq_addr):
        deq_addr <<= deq_addr + Const(1)


    # TODO: Make a switch construct

    with state == states.idle:
        clock_counter <<= Const(0)
        with ~io.uart_rx:
            state <<= states.start

    with state == states.start:
        with io.uart_rx & (clock_counter < Const(clocks_per_half_bit)):
            state <<= states.idle

        with clock_counter >= Const(clocks_per_bit):
            state <<= states.read
            clock_counter <<= Const(0)
            bit_counter <<= Const(0)

            for i in range(8):
                data_reg[i] <<= F

    with state == states.read:
        with clock_counter == clocks_per_half_bit:
            data_reg[bit_counter] <<= io.uart_rx

        with clock_counter == clocks_per_bit:
            with bit_counter == Const(7):
                state <<= states.stop
                clock_counter <<= Const(0)

            with otherwise:
                bit_counter <<= bit_counter + Const(1)
                clock_counter <<= 0

    with state == states.stop:
        with clock_counter == Const(clocks_per_bit):
            state <<= states.idle
            enqueue <<= T

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
    state = RegInit(Bits(states.bitwidth), states.idle)

    tx_buf = Reg(Bits(1, (8,)))

    clock_counter = RegInit(Bits(32), Const(0))
    bit_counter = RegInit(Bits(4), Const(0))

    data_reg = RegInit(Bits(8), Const(0))

    fifo_ram = Reg(Bits(8, (fifo_depth,)))
    enq_addr = RegInit(Bits(Log2Ceil(fifo_depth)), Const(0))
    deq_addr = RegInit(Bits(Log2Ceil(fifo_depth)), Const(0))
    enqueue = WireInit(Bits(1), F)

    data_count = RegInit(Bits(fifo_depth + 1), Const(0))
    full = Wire(Bits(1))
    empty = Wire(Bits(1))
    enqueue = WireInit(Bits(1), F)
    dequeue = WireInit(Bits(1), F)
    dequeue_data = Wire(Bits(8))

    full <<= data_count >= Const(fifo_depth)
    empty <<= data_count == Const(0)
    dequeue_data <<= fifo_ram[deq_addr]
    io.ready <<= ~full | dequeue

    with ~enqueue & dequeue:
        with ~empty:
            data_count <<= data_count - Const(1)
            deq_addr <<= deq_addr + Const(1)

    with enqueue & ~dequeue:
        with ~full:
            data_count <<= data_count + Const(1)
            enq_addr <<= enq_addr + Const(1)
            fifo_ram[enq_addr] <<= io.enqueue_data

    with enqueue & dequeue:
        deq_addr <<= deq_addr + Const(1)
        enq_addr <<= enq_addr + Const(1)
        fifo_ram[enq_addr] <<= io.enqueue_data

    with dequeue:
        for i in range(8):
            tx_buf[i] <<= dequeue_data(i, i)

    io.uart_tx <<= T
    clock_counter <<= clock_counter + Const(1)

    with state == states.idle:
        clock_counter <<= Const(0)
        bit_counter <<= Const(0)

        with ~empty:
            dequeue <<= T
            state <<= states.start

    with state == states.start:
        io.uart_tx <<= F
        with clock_counter > Const(clocks_per_bit):
            state <<= states.write


    with state == states.write:
        io.uart_tx <<= tx_buf[bit_counter]

        with clock_counter > Const(clocks_per_bit):
            with bit_counter == Const(7):
                state <<= states.stop
            with otherwise:
                bit_counter <<= bit_counter + Const(1)

    with state == states.stop:
        with clock_counter > Const(clocks_per_bit):
            state <<= states.idle

    NameSignals(locals())


circuit = Circuit()
with circuit:
    top = UartReceiver(50000000, 115200, 8)
    UartTransmitter(50000000, 115200, 8)

circuit.SetTop(top)
emitter.EmitFirrtl('uart.fir', circuit)
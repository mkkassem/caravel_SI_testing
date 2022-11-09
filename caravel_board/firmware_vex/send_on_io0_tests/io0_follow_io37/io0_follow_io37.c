#include "../../defs.h"
#include "../../gpio_config/gpio_config_io.c"
#include "../send_packet/send_packet_io.c"
//#include "../local_defs.h"
//#include "../stub.c"

//#include "../config_io.h"
//#include "../defs_mpw-two-mfix.h"


void set_registers() {

    reg_mprj_io_0 = GPIO_MODE_MGMT_STD_ANALOG;
    reg_mprj_io_1 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_2 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_3 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_4 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_5 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_6 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_7 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_8 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_9 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_10 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_11 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_12 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_13 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_14 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_15 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_16 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_17 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_18 = GPIO_MODE_MGMT_STD_OUTPUT;

    reg_mprj_io_19 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_20 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_21 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_22 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_23 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_24 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_25 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_26 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_27 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_28 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_29 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_30 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_31 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_32 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_33 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_34 = GPIO_MODE_MGMT_STD_OUTPUT;
//    reg_mprj_io_34 = 0x0403;
    reg_mprj_io_35 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_36 = GPIO_MODE_MGMT_STD_OUTPUT;
    reg_mprj_io_37 = GPIO_MODE_MGMT_STD_OUTPUT;
//    reg_mprj_io_37 = 0x0403;

}
/*

@ start sending on the higest gpios 
    send packet with size = 1
@ send 4 pulses at gpio[37]  
    send packet with size = 2
@ send 4 pulses at gpio[36]  
    send packet with size = 3
@ send 4 pulses at gpio[35]  
    send packet with size = 4
@ send 4 pulses at gpio[34]  
    send packet with size = 5
@ send 4 pulses at gpio[33]  
    send packet with size = 6
@ send 4 pulses at gpio[32]  
    send packet with size = 7
@ send 4 pulses at gpio[31]  
    send packet with size = 8
@ send 4 pulses at gpio[30]  
    send packet with size = 9
@ send 4 pulses at gpio[29]  
    send packet with size = 10

@ reset pulses
    send packet with size = 1
@ send 4 pulses at gpio[28]  
    send packet with size = 2
@ send 4 pulses at gpio[27]  
    send packet with size = 3
@ send 4 pulses at gpio[26]  
    send packet with size = 4
@ send 4 pulses at gpio[25]  
    send packet with size = 5
@ send 4 pulses at gpio[24]  
    send packet with size = 6
@ send 4 pulses at gpio[23]  
    send packet with size = 7
@ send 4 pulses at gpio[22]  
    send packet with size = 8
@ send 4 pulses at gpio[21]  
    send packet with size = 9
@ send 4 pulses at gpio[20]  
    send packet with size = 10
@ send 4 pulses at gpio[19]  
    send packet with size = 11

@ test finish 
    send packet with size = 1
    send packet with size = 1
    send packet with size = 1


*/
void main()
{
	int io37_mask = 0x20;
    int io0_mask = 0xFFFFFFFE;
    int io37;
    int io0;
    while (true){
        io37 = reg_mprj_datah >>5;
        io0  = reg_mprj_datal & io0_mask;
        reg_mprj_datal = io37 | io0;
    }

}


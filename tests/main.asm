    ORG 0
    MOV64 SP, stackTop
    CALL serial_init
    MOV64 G1, str
    CALL serial_write
    JMP exit

%INCLUDE "tests/serial.asm"

stackBottom:
    RES8 1024
stackTop:
    D8 0

str:
    D8 "Hello World from debugger!"
    D8 0

exit:   

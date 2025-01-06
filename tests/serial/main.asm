    ORG 0
    MOV64 SP, stackTop
    CALL serial_init
    MOV64 G1, str
    MOV64 G0, 79
    CALL serial_write
    CMP64 G0, 80
    JL test
    JMP exit

test:
    MOV64 G1, str2
    CALL serial_write
    JMP exit

%INCLUDE "tests/serial.asm"

stackBottom:
    RES8 1024
stackTop:
    D8 0

str:
    D8 "Hello World from debugger!"
    D8 10
    D8 0

str2:
    D8 "79 is less than 80"
    D8 10
    D8 0

exit:   

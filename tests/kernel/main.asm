    ORG 0x30000
    MOV64 SP, STK_TOP
MAIN:
    CALL NEWLINE
    CALL NEWLINE
    MOV64 G0, KMSG
    CALL PRINT
EXIT:
    JMP EXIT

KMSG: D8 "Hello world from Kernel loaded from Disk!" D8 0

STK_BOTTOM: RES8 1024
STK_TOP: D8 0

%INCLUDE "terminal.asm"
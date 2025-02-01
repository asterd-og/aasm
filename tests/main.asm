    MOV64 SP, STK_TOP
    JMP MAIN

COUNT_NUMS:
    ; Number = G0
    ; Result = G1
    PUSH64 G0
    MOV64 G1, 0
COUNT_NUMS_LOOP:
    CMP64 G0, 0
    JE COUNT_NUMS_EXIT
    ADD64 G1, 1
    DIV64 G0, 10
    JMP COUNT_NUMS_LOOP
COUNT_NUMS_EXIT:
    POP64 G0
    RET

PRINT_INT:
    ; Number = G0
    PUSH64 G1
    PUSH64 G2
    PUSH64 G3
    PUSH64 G4
    CALL COUNT_NUMS
    ADD32 G1, [CURSOR_X]
    MOV32 [CURSOR_X], G1
    ; Remove the next line when itoaing
    SUB32 G1, 1
PRINT_INT_LOOP:
    CMP64 G0, 0
    JE PRINT_INT_EXIT
    MOV64 G4, G0
    REM64 G4, 10
    ADD64 G4, 48
    MOV32 G2, [CURSOR_Y]
    MOV8 G3, G4
    CALL PUT_CHAR
    SUB32 G1, 1
    DIV64 G0, 10
    JMP PRINT_INT_LOOP
PRINT_INT_EXIT:
    CALL UPDATE_CURSOR
    POP64 G4
    POP64 G3
    POP64 G2
    POP64 G1
    RET

NEWLINE:
    MOV32 [CURSOR_X], 0
    ADD32 [CURSOR_Y], 1
    CALL UPDATE_CURSOR
    RET

MAIN:
    MOV64 G0, MEMORY
    CALL PRINT
    MOV64 G0, [0xC000]
    DIV64 G0, 1024 ; KB
    DIV64 G0, 1024 ; MB
    CALL PRINT_INT
    MOV64 G0, MB
    CALL PRINT
    JMP EXIT

MEMORY: D8 "Memory: " D8 0
MB: D8 " MB (MegaBytes)" D8 0

STK_BOTTOM: RES8 1024
STK_TOP: D8 0

%INCLUDE "tests/terminal.asm"

EXIT:
    JMP EXIT
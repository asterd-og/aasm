UPDATE_CURSOR:
    MOV32 [0x10000], [CURSOR_X]
    MOV32 [0x10004], [CURSOR_Y]
    RET

PUT_CHAR:
    ; X = G1
    ; Y = G2
    ; CH = G3
    ; COL = G4
    MOV64 G5, 0
    ; Y*WIDTH+X
    MOV32 G5, G2
    MUL32 G5, [0x10008]
    ADD32 G5, G1
    MUL32 G5, 2
    ADD32 G5, 0x10100
    SHL16 G4, 8
    OR16 G3, G4
    MOV16 [G5], G3
    RET

NEWLINE:
    ; TODO: Check for scroll
    MOV32 [CURSOR_X], 0
    ADD32 [CURSOR_Y], 1
    CALL UPDATE_CURSOR
    RET

PRINT:
    ; STR = G0
    PUSH64 G1
    PUSH64 G2
    PUSH64 G3
    PUSH64 G4
    MOV8 G4, 0x02
PRINT_LOOP:
    CMP8 [G0], 0
    JE PRINT_EXIT
    CMP8 [G0], 10
    JE PRINT_NL
    MOV32 G1, [CURSOR_X]
    MOV32 G2, [CURSOR_Y]
    MOV8 G3, [G0]
    CALL PUT_CHAR
    ADD32 [CURSOR_X], 1
    CALL UPDATE_CURSOR
    ADD64 G0, 1
    JMP PRINT_LOOP
PRINT_NL:
    CALL NEWLINE
    ADD64 G0, 1
    JMP PRINT_LOOP
PRINT_EXIT:
    POP64 G4
    POP64 G3
    POP64 G2
    POP64 G1
    RET

PRINT_COLOR:
    ; STR = G0
    ; COLOR = G1
    PUSH64 G4
    MOV8 G4, G1
    PUSH64 G2
    PUSH64 G3
PRINTC_LOOP:
    CMP8 [G0], 0
    JE PRINTC_EXIT
    CMP8 [G0], 10
    JE PRINTC_NL
    MOV32 G1, [CURSOR_X]
    MOV32 G2, [CURSOR_Y]
    MOV8 G3, [G0]
    CALL PUT_CHAR
    ADD32 [CURSOR_X], 1
    CALL UPDATE_CURSOR
    ADD64 G0, 1
    JMP PRINTC_LOOP
PRINTC_NL:
    CALL NEWLINE
    ADD64 G0, 1
    JMP PRINTC_LOOP
PRINTC_EXIT:
    POP64 G3
    POP64 G2
    POP64 G4
    RET

CURSOR_X: D32 0
CURSOR_Y: D32 0
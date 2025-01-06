serial_init:
    MOV64 [serial_addr], [0x1008]
    RET

    ;; Sends character when bus is idle
serial_write:
    PUSH64 G0
    PUSH64 G1
    PUSH64 G2
    MOV64 G0, [serial_addr]
serial_write_busy:
    MOV8 G2, [G0]
    CMP8 G2, 0
    JE serial_write_continue
    JMP serial_write_busy
serial_write_continue:
    MOV8 G2, [G1]
    CMP8 G2, 0
    JE serial_write_exit
    MOV8 [G0], G2
    ADD64 G1, 1
    JMP serial_write_busy
serial_write_exit:
    POP64 G2
    POP64 G1
    POP64 G0
    RET

serial_addr:
    D64 0

// SPDX-License-Identifier: MIT

`default_nettype none

interface r5900_debug_if;

    import r5900_types_pkg::*;

    r5900_arch_state_t            arch_state;
    r5900_instruction_t           instruction;
    r5900_writeback_t             writeback;
    r5900_reserved_instruction_t reserved_instruction;

    modport producer (
        output arch_state,
        output instruction,
        output writeback,
        output reserved_instruction
    );

    modport monitor (
        input arch_state,
        input instruction,
        input writeback,
        input reserved_instruction
    );

endinterface

`default_nettype wire

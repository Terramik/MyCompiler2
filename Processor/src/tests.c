#include "../include/base.h"
#include "../include/utils.h"
#include "../include/execute.h"


#define TEST_NAME(name) test_##name
#define RANDOM_RAM_START 0xf0


/* for regs values checks with non-default values */
typedef struct
{
    uint8_t id;
    uint32_t val;
} ExpectedReg;


bool CheckRegs(
    CPU* cpu, const char* id, 
    ExpectedReg* exp_reg_start, size_t exp_reg_len, 
    size_t program_len) {
    size_t expected_reg_i = 0;
    size_t reg_i = 0;

    while (reg_i < 16)
    {
        uint32_t expected;
        bool inc_exp_reg = false;

        // non-default, if there is non-default val, and it is current reg
        if ( expected_reg_i < exp_reg_len && exp_reg_start[expected_reg_i].id == reg_i ) {
            expected = exp_reg_start[expected_reg_i].val;
            inc_exp_reg = true;
        // default
        } else {
            switch (reg_i)
            {
                case REGISTER_CP:
                    expected = 0xfff0 + program_len - 1; break;
                case REGISTER_FL:
                    expected = 0; break;
                case REGISTER_SF:
                    expected = 0x0ff0; break;
                default:
                    expected = 42; break;
            }
        }
        
        // check itself
        if ( cpu->registers[reg_i] != expected ) {
            printf("%s: r%2d: %10d, expected: %10d\n", id, reg_i, cpu->registers[reg_i], expected);
            return false;
        }

        // incs
        if ( inc_exp_reg )
            expected_reg_i++;
        reg_i++;
    }

    return true;
}


bool static inline CheckRAM_IsSame(
    CPU* cpu, const char* id, 
    size_t i, uint8_t expected
) {
    if ( cpu->RAM[i] != expected ) {
        printf("%s: %10d: %10d, expected: %10d", id, i, cpu->RAM[i], expected);
        return false;
    }
    return true;
}

bool CheckRAM(
    CPU* cpu, const char* id, 
    uint8_t* ram_start, size_t ram_len, 
    uint8_t* code_start, size_t code_len
) {
    size_t i = 0;

    // from start to ram
    while (i < RANDOM_RAM_START)
        if ( !CheckRAM_IsSame(cpu, id, i++, 42) )
            return false;

    // ram
    if ( ram_len > 0 ) {
        size_t ram_i = 0;
        while (ram_i < ram_len)
            if ( !CheckRAM_IsSame(cpu, id, i++, ram_start[ram_i++]) )
                return false;
    }
    
    // from ram to code
    while (i < 0xfff0)
        if ( !CheckRAM_IsSame(cpu, id, i++, 42) )
            return false;

    // code
    {
        size_t code_i = 0;
        while (code_i < code_len)
            if ( !CheckRAM_IsSame(cpu, id, i++, code_start[code_i++]) )
                return false;
    }

    // from code to end
    while (i < RAM_SIZE)
        if ( !CheckRAM_IsSame(cpu, id, i++, 42) )
            return false;
    
    return true;
}


bool CheckAll(
    const char* id, 
    uint8_t* ram_start, size_t ram_len, 
    uint8_t* code_start, size_t code_len,
    ExpectedReg* exp_reg_start, size_t exp_reg_len
) {
    CPU cpu;
    if ( !CPU_Init(&cpu) ) {
        printf("%s: Processor init failed", id);
        return false;
    }
    for (size_t i = 0; i < RAM_SIZE; i++)
        cpu.RAM[i] = 42;
    CPU_LoadProgram_FromArray(&cpu, code_start, code_len);
    CPU_ExecuteAll(&cpu);

    bool res = CheckRegs(&cpu, id, exp_reg_start, exp_reg_len, code_len) &&
               CheckRAM(&cpu, id, ram_start, ram_len, code_start, code_len);
    CPU_Del(&cpu);
    return res;
}

/*
    code - executable byte-code.
    ram - for command that works with RAM(starts from RANDOM_RAM_START).
    expected_reg - if value in them are not by default, id's in ascending order.
*/
#define MAKE_TEST(name, code, ram, expected_reg) \
{ \
    const char* id = #name; \
    uint8_t _ram[] = ram; \
    uint8_t _code[] = code; \
    ExpectedReg _regs[] = expected_reg; \
    if ( !CheckAll(id, _ram, sizeof(_ram), _code, sizeof(_code), _regs, sizeof(_regs) / sizeof(ExpectedReg)) ) \
        return 1; \
}

#define MAKE_ARRAY(...) {__VA_ARGS__}


int main() {

    MAKE_TEST(
        STOP, 
        MAKE_ARRAY(0x10), // STOP
        MAKE_ARRAY(),
        MAKE_ARRAY()
    )

    MAKE_TEST(
        PASS, 
        MAKE_ARRAY(0x11, 0x11, 0x10), // PASS PASS STOP
        MAKE_ARRAY(),
        MAKE_ARRAY()
    )

    MAKE_TEST(
        MOVE, 
        MAKE_ARRAY(0x20, 0xe2, 0x10), // MOVE r2 r14(FL) STOP
        MAKE_ARRAY(),
        MAKE_ARRAY((ExpectedReg){2, 0})
    )

    MAKE_TEST(
        CONST, 
        MAKE_ARRAY(
            // CONST r9 3
            0x2c, 0x09, 0x00, 0x00, // CONST r9
            3, 0x00, 0x00, 0x00, // 3
            0x10 // STOP
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY((ExpectedReg){9, 3})
    )

    MAKE_TEST(
        SAVE_WORD, 
        MAKE_ARRAY(
            0x2d, 0x01, 0x06, 0x00, // CONST_HALF r1 6
            0x2d, 0x02, 0xf0, 0x00, // CONST_HALF r2 0xf0
            0x35, 0x12, // SAVE WORD r2 r1
            0x10 // STOP
        ), 
        MAKE_ARRAY(
            6, 0, 0, 0
        ),
        MAKE_ARRAY(
            (ExpectedReg){1, 6},
            (ExpectedReg){2, 0xf0}
        )
    )

    MAKE_TEST(
        JUMP_IF, 
        MAKE_ARRAY(
            0x2d, 0x0e, 0x01, 0x00, // CONST_HALF r14(FL) 1
            // JUMP IF 9(to second STOP)
            0x49, 0x00, 0x00, 0x00, // JUMP IF
            9, 0x00, 0x00, 0x00, // 9
            0x10, // first STOP, if it doesn't jump - stop here. 
            0x10 // second, STOP, if it does jump - stop here, we can detect it with CP value.
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){14, 1}
        )
    )

    MAKE_TEST(
        JUMP_IF, 
        MAKE_ARRAY(
            0x49, 0x00, 0x00, 0x00, // JUMP IF
            9, 0x00, 0x00, 0x00, // 9
            0x10, // should stop here, as FL is 0
            0x10 
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){15, 0xfff0 + 8} // expected CP, first STOP
        )
    )

    // COMP

    MAKE_TEST(
        COMP_ZERO, 
        MAKE_ARRAY(
            0x2d, 0x02, 0x00, 0x00, // CONST_HALF r2 0
            0x21, 0x02,             // COMP r2
            0x10                    // STOP
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){2, 0},
            (ExpectedReg){14, 0x3}  // ZR | PS
        )
    )

    MAKE_TEST(
        COMP_POS, 
        MAKE_ARRAY(
            0x2d, 0x02, 0x05, 0x00, // CONST_HALF r2 5
            0x21, 0x02,             // COMP r2
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){2, 5},
            (ExpectedReg){14, 0x2}  // PS
        )
    )

    MAKE_TEST(
        COMP_NEG, 
        MAKE_ARRAY(
            0x2c, 0x02, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, // CONST r2 0xffffffff
            0x21, 0x02,                                     // COMP r2
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){2, 0xffffffff} // FL = 0 (ZR=0, PS=0)
        )
    )

    MAKE_TEST(
        CONST_HALF_ZEROES_UPPER, 
        MAKE_ARRAY(
            0x2d, 0x01, 0x34, 0x12, // CONST_HALF r1 0x1234
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0x1234}
        )
    )

    
    // OP

    MAKE_TEST(
        OP_ADD, 
        MAKE_ARRAY(
            0x2d, 0x01, 0x05, 0x00, // CONST_HALF r1 5
            0x2d, 0x02, 0x03, 0x00, // CONST_HALF r2 3
            0x22, 0x21,             // OP ADD r1 r2
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 8},
            (ExpectedReg){2, 3}
        )
    )

    MAKE_TEST(
        OP_ADD_CARRY, 
        MAKE_ARRAY(
            0x2c, 0x01, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, // CONST r1 0xffffffff
            0x2d, 0x02, 0x01, 0x00,                         // CONST_HALF r2 1
            0x22, 0x21,                                     // OP ADD -> r1=0, CR=1
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0},
            (ExpectedReg){2, 1},
            (ExpectedReg){14, 0x4}  // CR
        )
    )

    MAKE_TEST(
        OP_ADD_M, 
        MAKE_ARRAY(
            0x2d, 0x01, 0x05, 0x00, // CONST_HALF r1 5
            0x2d, 0x02, 0x03, 0x00, // CONST_HALF r2 3
            0x23, 0x21,             // OP ADD_M (CR=0 -> 5+3+0=8)
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 8},
            (ExpectedReg){2, 3}
        )
    )

    // 0xffffffff + 1 -> 0, CR=1; затем 0xffffffff + 0 + 1 -> 0, CR=1
    MAKE_TEST(
        OP_ADD_M_CARRY, 
        MAKE_ARRAY(
            0x2c, 0x01, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, // CONST r1 0xffffffff
            0x2d, 0x02, 0x01, 0x00,                         // CONST_HALF r2 1
            0x22, 0x21,                                     // OP ADD -> r1=0, CR=1
            0x2c, 0x01, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, // CONST r1 0xffffffff
            0x2d, 0x02, 0x00, 0x00,                         // CONST_HALF r2 0
            0x23, 0x21,                                     // OP ADD_M -> r1=0, CR=1
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0},
            (ExpectedReg){2, 0},
            (ExpectedReg){14, 0x4}  // CR
        )
    )

    MAKE_TEST(
        OP_SUB, 
        MAKE_ARRAY(
            0x2d, 0x01, 0x0a, 0x00, // CONST_HALF r1 10
            0x2d, 0x02, 0x03, 0x00, // CONST_HALF r2 3
            0x24, 0x21,             // OP SUB -> 7
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 7},
            (ExpectedReg){2, 3}
        )
    )

    MAKE_TEST(
        OP_NEG, 
        MAKE_ARRAY(
            0x2d, 0x02, 0x05, 0x00, // CONST_HALF r2 5
            0x25, 0x21,             // OP NEG r1 r2 -> -5
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0xfffffffb},
            (ExpectedReg){2, 5}
        )
    )

    MAKE_TEST(
        OP_AND, 
        MAKE_ARRAY(
            0x2d, 0x01, 0x0c, 0x00, // CONST_HALF r1 12
            0x2d, 0x02, 0x0a, 0x00, // CONST_HALF r2 10
            0x26, 0x21,             // OP AND -> 8
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 8},
            (ExpectedReg){2, 10}
        )
    )

    MAKE_TEST(
        OP_OR, 
        MAKE_ARRAY(
            0x2d, 0x01, 0x0c, 0x00, // CONST_HALF r1 12
            0x2d, 0x02, 0x0a, 0x00, // CONST_HALF r2 10
            0x27, 0x21,             // OP OR -> 14
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 14},
            (ExpectedReg){2, 10}
        )
    )

    MAKE_TEST(
        OP_XOR, 
        MAKE_ARRAY(
            0x2d, 0x01, 0x0c, 0x00, // CONST_HALF r1 12
            0x2d, 0x02, 0x0a, 0x00, // CONST_HALF r2 10
            0x28, 0x21,             // OP XOR -> 6
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 6},
            (ExpectedReg){2, 10}
        )
    )

    MAKE_TEST(
        OP_NOT, 
        MAKE_ARRAY(
            0x2d, 0x02, 0x00, 0x00, // CONST_HALF r2 0
            0x29, 0x21,             // OP NOT -> 0xffffffff
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0xffffffff},
            (ExpectedReg){2, 0}
        )
    )

    MAKE_TEST(
        OP_SHL, 
        MAKE_ARRAY(
            0x2d, 0x02, 0x05, 0x00, // CONST_HALF r2 5
            0x2a, 0x21,             // OP SHL -> 10, CR=0
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 10},
            (ExpectedReg){2, 5}
        )
    )

    MAKE_TEST(
        OP_SHL_CARRY, 
        MAKE_ARRAY(
            0x2c, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, // CONST r2 0x80000000
            0x2a, 0x21,                                     // OP SHL -> 0, CR=1
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0},
            (ExpectedReg){2, 0x80000000},
            (ExpectedReg){14, 0x4}
        )
    )

    MAKE_TEST(
        OP_SHR, 
        MAKE_ARRAY(
            0x2d, 0x02, 0x04, 0x00, // CONST_HALF r2 4
            0x2b, 0x21,             // OP SHR -> 2, CR=0
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 2},
            (ExpectedReg){2, 4}
        )
    )

    MAKE_TEST(
        OP_SHR_CARRY, 
        MAKE_ARRAY(
            0x2d, 0x02, 0x05, 0x00, // CONST_HALF r2 5
            0x2b, 0x21,             // OP SHR -> 2, CR=1
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 2},
            (ExpectedReg){2, 5},
            (ExpectedReg){14, 0x4}
        )
    )

    // LOAD

    MAKE_TEST(
        LOAD_BYTE, 
        MAKE_ARRAY(
            0x2d, 0x02, 0xf0, 0xff, // CONST_HALF r2 0xfff0
            0x30, 0x21,             // LOAD BYTE r1 r2
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0x2d},
            (ExpectedReg){2, 0xfff0}
        )
    )

    MAKE_TEST(
        LOAD_HALF, 
        MAKE_ARRAY(
            0x2d, 0x02, 0xf0, 0xff, // CONST_HALF r2 0xfff0
            0x31, 0x21,             // LOAD HALF r1 r2 (little-endian)
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0x022d},
            (ExpectedReg){2, 0xfff0}
        )
    )

    MAKE_TEST(
        LOAD_WORD, 
        MAKE_ARRAY(
            0x2d, 0x02, 0xf0, 0xff, // CONST_HALF r2 0xfff0
            0x32, 0x21,             // LOAD WORD r1 r2
            0x10
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){1, 0xfff0022d},
            (ExpectedReg){2, 0xfff0}
        )
    )

    // SAVE

    MAKE_TEST(
        SAVE_BYTE, 
        MAKE_ARRAY(
            0x2d, 0x01, 0xab, 0x00, // CONST_HALF r1 0xab
            0x2d, 0x02, 0xf0, 0x00, // CONST_HALF r2 0xf0
            0x33, 0x12,             // SAVE BYTE r2 r1 (пишем только младший байт)
            0x10
        ), 
        MAKE_ARRAY(
            0xab
        ),
        MAKE_ARRAY(
            (ExpectedReg){1, 0xab},
            (ExpectedReg){2, 0xf0}
        )
    )

    MAKE_TEST(
        SAVE_HALF, 
        MAKE_ARRAY(
            0x2d, 0x01, 0xcd, 0xab, // CONST_HALF r1 0xabcd
            0x2d, 0x02, 0xf0, 0x00, // CONST_HALF r2 0xf0
            0x34, 0x12,             // SAVE HALF r2 r1 (little-endian)
            0x10
        ), 
        MAKE_ARRAY(
            0xcd, 0xab
        ),
        MAKE_ARRAY(
            (ExpectedReg){1, 0xabcd},
            (ExpectedReg){2, 0xf0}
        )
    )

    // JUMP: 

    MAKE_TEST(
        JUMP_NO, 
        MAKE_ARRAY(
            0x40, 0x00, 0x00, 0x00, // JUMP NO
            0x09, 0x00, 0x00, 0x00, // dist 9
            0x10,                   // first STOP (skip)
            0x10                    // second STOP (land)
        ), 
        MAKE_ARRAY(),
        MAKE_ARRAY(
            (ExpectedReg){15, 0xfff0 + 9}
        )
    )

    printf("Everything is good\n");
    return 0;
}

// cd C:\Coding\Python\Two\Test\TheLanguage\TrueHardVersionV2\Processor
// gcc src\main.c src\utils.c src\execute.c -o cpu


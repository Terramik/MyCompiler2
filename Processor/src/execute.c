#include "../include/execute.h"



typedef enum {
    ExitCode_Okay,
    ExitCode_Error,
    ExitCode_Stop
} ExitCode;


ExitCode CPU_ExecuteOne(CPU* cpu) {

    #define RAM(indx) cpu->RAM[indx]
    #define REG(indx) cpu->registers[indx]
    #define CP REG(REGISTER_CP)
    #define FL REG(REGISTER_FL)

    #define HALF_ACCESS(thing) (*((uint16_t*)(&(thing))))
    #define WORD_ACCESS(thing) (*((uint32_t*)(&(thing))))

    #define FIRST_BYTE (RAM(CP))
    #define SECOND_BYTE (RAM(CP + 1))
    #define FIRST_4_BIT (SECOND_BYTE & 0xf)
    #define SECOND_4_BIT (SECOND_BYTE >> 4)
    #define SECOND_HALF HALF_ACCESS(RAM(CP + 2))
    #define SECOND_WORD WORD_ACCESS(RAM(CP + 4))

    #define R1 REG(FIRST_4_BIT)
    #define R2 REG(SECOND_4_BIT)

    #define READ_BIT(from, indx) (((from) >> (indx)) & 1)
    #define SET_BIT(to, indx, val) \
        if ( (val) == 0 ) { \
            (to) &= ~(1 << (indx)); \
        } else { \
            (to) |= 1 << (indx); \
        }


    switch (FIRST_BYTE)
    {
        case 0x10: { // STOP
            return ExitCode_Stop;
        } break;

        case 0x11: { // PASS
            CP += 1;
        } break;


        case 0x20: { // MOVE
            R1 = R2;
            CP += 2;
        } break;

        case 0x21: { // COMP
            SET_BIT(FL, FLAG_ZR, R1 == 0)
            SET_BIT(FL, FLAG_PS, R1 >> 31 == 0)
            CP += 2;
        } break;

        case 0x2c: { // CONST
            R1 = SECOND_WORD;
            CP += 8;
        } break;

        case 0x2d: { // CONST_HALF
            R1 = SECOND_HALF;
            CP += 4;
        } break;
        
        // OP 
        case 0x22: { // ADD
            uint64_t res = (uint64_t)R1 + (uint64_t)R2;
            R1 = (uint32_t)res;
            SET_BIT(FL, FLAG_CR, res > UINT32_MAX)
            CP += 2;
        } break;
        case 0x23: { // ADD_M
            uint64_t res = (uint64_t)R1 + (uint64_t)R2 + READ_BIT(FL, FLAG_CR);
            R1 = (uint32_t)res;
            SET_BIT(FL, FLAG_CR, res > UINT32_MAX)
            CP += 2;
        } break;
        case 0x24: { // SUB
            R1 -= R2;
            CP += 2;
        } break;
        case 0x25: { // NEG
            R1 = -R2;
            CP += 2;
        } break;
        case 0x26: { // AND
            R1 &= R2;
            CP += 2;
        } break;
        case 0x27: { // OR
            R1 |= R2;
            CP += 2;
        } break;
        case 0x28: { // XOR
            R1 ^= R2;
            CP += 2;
        } break;
        case 0x29: { // NOT
            R1 = ~R2;
            CP += 2;
        } break;
        case 0x2a: { // SHL
            SET_BIT(FL, FLAG_CR, R2 >> 31)
            R1 = R2 << 1;
            CP += 2;
        } break;
        case 0x2b: { // SHR
            SET_BIT(FL, FLAG_CR, R2 & 1)
            R1 = R2 >> 1;
            CP += 2;
        } break;
        
        // LOAD AND SAVE
        #define ALIGN_CHECK(index, step) \
            if ( index % step != 0 ) { \
                printf("Critical error: non-aligned memory access\n"); \
                return ExitCode_Error; \
            }

        // BYTE
        case 0x30: {
            R1 = RAM(R2);
            CP += 2;
        } break;
        case 0x33: {
            RAM(R1) = R2;
            CP += 2;
        } break;

        // HALF
        case 0x31: {
            ALIGN_CHECK(R2, 2)
            R1 = HALF_ACCESS(RAM(R2));
            CP += 2;
        } break;
        case 0x34: {
            ALIGN_CHECK(R1, 2)
            HALF_ACCESS(RAM(R1)) = R2;
            CP += 2;
        } break;
        
        // WORD
        case 0x32: {
            ALIGN_CHECK(R2, 4)
            R1 = WORD_ACCESS(RAM(R2));
            CP += 2;
        } break;
        case 0x35: {
            ALIGN_CHECK(R1, 4)
            WORD_ACCESS(RAM(R1)) = R2;
            CP += 2;
        } break;
        
        // JUMP
        #define JUMP_IF(condition) \
            if ( condition ) { \
                CP += (int32_t)SECOND_WORD; \
            } else { \
                CP += 8; \
            }
        #define ZR (READ_BIT(FL, FLAG_ZR))
        #define PS (READ_BIT(FL, FLAG_PS))
        #define CR (READ_BIT(FL, FLAG_CR))

        case 0x40: { // NO
            JUMP_IF( true )
        } break;
        case 0x41: { // CR
            JUMP_IF( CR )
        } break;
        case 0x42: { // NC
            JUMP_IF( !CR )
        } break;
        case 0x43: { // ZR
            JUMP_IF( ZR )
        } break;
        case 0x44: { // NZ
            JUMP_IF( !ZR )
        } break;
        case 0x45: { // GT
            JUMP_IF( !ZR && PS )
        } break;
        case 0x46: { // GE
            JUMP_IF( PS )
        } break;
        case 0x47: { // LT
            JUMP_IF( !ZR && !PS )
        } break;
        case 0x48: { // LE
            JUMP_IF( !PS || ZR )
        } break;
        case 0x49: { // IF
            JUMP_IF( FL != 0 )
        } break;
                    
        default:
            printf("Critical error: unknow opcode\n");
            return ExitCode_Error;
    }

    return ExitCode_Okay;
}



bool CPU_ExecuteAll(CPU* cpu) {
    ExitCode res;

    while (true)
    {
        res = CPU_ExecuteOne(cpu);
        switch (res) {
            case ExitCode_Stop:
                return true;
            case ExitCode_Error:
                return false;
            case ExitCode_Okay:
                break;
        }
    }
}


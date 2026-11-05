#include "../include/base.h"
#include "../include/utils.h"
#include "../include/execute.h"


#define command_src "C:/Coding/Python/Two/Test/TheLanguage/TrueHardVersionV2/Processor/program.bin"
// "program.bin"

int main() {
    CPU cpu;
    
    if ( !CPU_Init(&cpu) ) {
        printf("Initialization failed\n");
        return 1;
    }

    if ( !CPU_LoadProgram_FromFile(&cpu, command_src) ) {
        printf("Program load failed\n");
        CPU_Del(&cpu);
        return 1;
    }

    if ( !CPU_ExecuteAll(&cpu) ) {
        printf("Execition failed\n");
        CPU_Del(&cpu);
        return 1;
    }


    CPU_PrintState_Registers(&cpu);


    CPU_Del(&cpu);
    return 0;
}

// cd C:\Coding\Python\Two\Test\TheLanguage\TrueHardVersionV2\Processor
// gcc src\main.c src\utils.c src\execute.c -o cpu

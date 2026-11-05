#include "../include/utils.h"


bool CPU_Init(CPU* cpu) {
    uint8_t* ram = malloc(RAM_SIZE * sizeof(uint8_t));
    if ( ram == NULL ) {
        printf("Memory allocation failed\n");
        return false;   
    }

    cpu->RAM = ram;

    for (size_t i = 0; i < 16; i++) {
        cpu->registers[i] = 42;
    }

    cpu->registers[REGISTER_CP] = 0xfff0;
    cpu->registers[REGISTER_FL] = 0;
    cpu->registers[REGISTER_SF] = 0x0ff0;
                
    return true;
}


void CPU_Del(CPU* cpu) {
    free(cpu->RAM);
}


bool CPU_LoadProgram_FromFile(CPU* cpu, const char* path) {
    FILE* file = fopen(path, "rb");

    if ( file == NULL ) {
        printf("File access failed: %s\n", strerror(errno));
        return false;
    }

    size_t file_i = 0xfff0;

    while (file_i <= RAM_SIZE)
    {
        int readed = getc(file);
        
        if ( readed == EOF )
            break;


        cpu->RAM[file_i] = (uint8_t)readed;

        if ( file_i == RAM_SIZE ) {
            printf("Program is too big\n");
            fclose(file);
            return false;
        }
        file_i++;
    }

    if ( ferror(file) ) {
        printf("Error on program read: %s\n", strerror(errno));
        fclose(file);
        return false;
    }
    
    fclose(file);
    return true;
}


void CPU_LoadProgram_FromArray(CPU* cpu, uint8_t* start, size_t len) {
    size_t ram_i = 0xfff0;
    size_t array_i = 0;

    while (array_i < len)
        cpu->RAM[ram_i++] = start[array_i++];
}


void CPU_PrintState_Registers(CPU* cpu) {
    for (size_t i = 0; i < 16; i++) {
        printf("r%-2d: 0x%08x %10d\n", i, cpu->registers[i], cpu->registers[i]);
    }
}


void CPU_PrintState_RAM(CPU* cpu, size_t start, size_t end) {
    for (size_t i = start; i < end; i++) {
        printf("%08x: 0x%08x %10d\n", i, cpu->RAM[i], cpu->RAM[i]);
    }
}


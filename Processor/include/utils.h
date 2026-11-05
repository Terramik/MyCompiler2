

#ifndef UTILS_H
#define UTILS_H

#include "base.h"


bool CPU_Init(CPU* cpu);

void CPU_Del(CPU* cpu);


bool CPU_LoadProgram_FromFile(CPU* cpu, const char* path);

void CPU_LoadProgram_FromArray(CPU* cpu, uint8_t* start, size_t len);


void CPU_PrintState_Registers(CPU* cpu);

/* prints in range [start:end) */
void CPU_PrintState_RAM(CPU* cpu, size_t start, size_t end);


#endif


#ifndef BASE_H
#define BASE_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <errno.h>
#include <string.h>


typedef struct
{
    uint32_t registers[16];
    uint8_t* RAM;
} CPU;


#define REGISTER_CP 15
#define REGISTER_FL 14
#define REGISTER_SF 13

#define RAM_SIZE 0x1000000

#define FLAG_ZR 0
#define FLAG_PS 1
#define FLAG_CR 2

#endif
#ifndef __AD9833_H_
#define __AD9833_H_



#include "sys.h"
#include "spi.h"



#define AD9833_SYSTEM_CLOCK  25000000
#define FREQ_0               0

void AD9833_Init(void);
void AD9833_SelectWave(u8 select);
void AD9833_SetFreq(u32 _freq);




#endif

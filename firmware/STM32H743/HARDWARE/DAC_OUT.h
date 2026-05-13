#ifndef __DAC_OUT_H_
#define __DAC_OUT_H_

#include "sys.h" 
#include "usart.h"

void DAC_Init(void);
void Dac1_Set_Vol(u8 L_R,u32 vol);



#endif

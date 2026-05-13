#ifndef __PUSE_CAPTURE_
#define __PUSE_CAPTURE_

#define  DUAL_MODE 
//#define  SINGLE_MODE 

#include "sys.h"
#include "usart.h"

void TIM5_CH1_3_Cap_Init(u32 arr,u16 psc);
float Read_Puse(u8 mode);

#endif

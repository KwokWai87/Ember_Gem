#ifndef __MCU_ADC_H_
#define __MCU_ADC_H_



#include "sys.h"
#include "delay.h"
#include "arm_math.h" 
#include "usart.h"	

#define SDRAM_AREA_ATTRIBUTE  __attribute__ ((section("in_axi_sram")))

void ADC1_2_Init(u8 simpr,u16 OSVR, u8 OVSS,u8 JOVSE,u8 ROVSE,u32  length);
float Read_Mcu_ADC(u8 ch);
void MYDMA_Config(DMA_Stream_TypeDef *DMA_Streamx,u8 chx,u32 par,u32 mar,u16 ndtr,u8 model,u8 dir);
void ADC_BUFFER_READ(u8 model,int32_t Adc_Zero_Offset);

#endif

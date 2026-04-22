#ifndef __ADS1219_H_
#define __ADS1219_H_


#include "sys.h"
#include "S_IIC.h"

#define IO_ADC_RST(x)  GPIO_Pin_Set(GPIOG,PIN0,x)	
#define IO_ADC_DRDY    GPIO_Pin_Get(GPIOG,PIN1)	

#define ADS1219_ADDRESS         0x80

#define ADS1219_CMD_RESET       0x06 
#define ADS1219_CMD_START       0x08 
#define ADS1219_CMD_POWERDOWN   0x02
#define ADS1219_CMD_RDATA       0x10
#define ADS1219_CMD_RREG        0x20
#define ADS1219_CMD_WREGE       0x40

//#define ADS1219_CFG_REG         0x00
//#define ADS1219_STATUS_REG      0x01

#define ADS1219_VREF_BIT        0
#define ADS1219_CM_BIT          1
#define ADS1219_DR_BIT          2
#define ADS1219_GAIN_BIT        4
#define ADS1219_MUX_BIT         5
#define ADS1219_DRDY_BIT        7
#define ADS1219_ID_BIT          0

#define ADS1219_MUX0    0//AINP = AIN0, AINN = AIN1 (default)
#define ADS1219_MUX1    1//AINP = AIN2, AINN = AIN3
#define ADS1219_MUX2    2//AINP = AIN1, AINN = AIN2
#define ADS1219_MUX3    3//AINP = AIN0, AINN = AGND
#define ADS1219_MUX4    4//AINP = AIN1, AINN = AGND
#define ADS1219_MUX5    5//AINP = AIN2, AINN = AGND
#define ADS1219_MUX6    6//AINP = AIN3, AINN = AGND
#define ADS1219_MUX7    7//AINP and AINN shorted to AVDD / 2

#define ADS1219_GAINx1  0//Gain = 1 (default)
#define ADS1219_GAINx4  1//Gain = 4

#define ADS1219_DR0     0//20 SPS (default)
#define ADS1219_DR1     1//90 SPS
#define ADS1219_DR2     2//330 SPS
#define ADS1219_DR3     3//1000 SPS

#define ADS1219_CM0     0//Single-shot conversion mode (default)
#define ADS1219_CM1     1//Continuous conversion mode

#define ADS1219_VREF0   0//Internal 2.048-V reference selected (default)
#define ADS1219_VREF1   1//External reference selected using the REFP and REFN inputs


void ADS1219_init(u8 mux,u8 gain,u8 dr,u8 cm,u8 vref);
void ADS1219_Read_vol(void);



#endif 

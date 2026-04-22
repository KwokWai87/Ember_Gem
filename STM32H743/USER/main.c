#include "sys.h" 
#include "usart.h" 
#include "delay.h" 
#include "led.h" 
#include "spi.h" 
#include "norflash.h"
#include "mpu.h"
#include "w25qxx.h"
#include "usmart.h"
#include "POWER_IO.h"
#include "MCP4725A.h"
#include "24AA025E48T.h"
#include "qspi.h"
#include "APS6404L.h"
#include "DAC_OUT.h"
#include "ADS1219.h"
#include "CH446Q.h"
#include "DG4052EEQ.h"
#include "AD9851.h"
#include "PGA849.h"
#include "AD9833.h"
#include "TLV3502AID.h"
#include "PUSE_CAPTURE.h"
#include "MCU_ADC.h"
#include "AAF_IO.h"
#include "DisCharge.h"


const u8 TEXT_Buffer[]={"Polaris STM32H7 QSPI TEST"};
#define SIZE sizeof(TEXT_Buffer)
u8 debug=0;	
extern u32 ADC_BUFFER_SIZE;
int main(void)
{ 
//	u32 flashsize=8*1024*1024;
	Stm32_Clock_Init(160,5,4,4);	//设置时钟,200Mhz
	MPU_Memory_Protection();		  //保护相关存储区域
  delay_init(200);				      //延时初始化
	uart_init(50,921600);			   //串口初始化
	usmart_dev.init(100); 			  //初始化USMART	
	ADC1_2_Init(0,0,0,0,0,ADC_BUFFER_SIZE);
	IIC1_Init();
	IIC4_Init();
	SPI2_Init();
	SPI4_Init();	
	QSPI_Init();
  POWER_IO_Init();
	TLV3502AID_init();
	DG4052EEQ_Init();
	AD9851_init();
	AD9833_Init();
	LED_Init();
  EEPROM_Init();
	DAC_Init();
  W25QXX_Init();
  CH446Q_init();
	AAF_IO_Init();
	PGA849_init();
	ADS1219_init(0,0,0,0,0);
	APS6404L_Init();
	MCP4725A_init(1);
	MCP4725A_init(2);
	DisCharge_Init();
//	TIM5_CH1_3_Cap_Init(0xFFFFFFFF,10-1);//100ns
//	 MCP4725A_Set_Voltage(1, SAVE,OUT_ON,2.5f);
//	 MCP4725A_Set_Voltage(2, SAVE,OUT_ON,2.5f);
	
//  NORFLASH_Init();
	while(1)
	{
		LEDR(0);
		LEDG(0);
		LEDB(0);
		delay_ms(500);
		LEDR(1);
		LEDG(1);
		LEDB(1);
//		NORFLASH_Read(datatemp,flashsize-100,SIZE);					//从倒数第100个地址处开始,读出SIZE个字节
		delay_ms(500);	
    if(debug)
		{
		debug=0;
//		NORFLASH_Erase_Chip();
//		NORFLASH_Write((u8*)TEXT_Buffer,flashsize-100,SIZE);		//从倒数第100个地址处开始,写入SIZE长度的数据	
		}			
	}
}

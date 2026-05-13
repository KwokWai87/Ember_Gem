#include "usmart.h"
#include "usmart_str.h"
////////////////////////////用户配置区///////////////////////////////////////////////
//这下面要包含所用到的函数所申明的头文件(用户自己添加) 
#include "delay.h"	 	
#include "POWER_IO.h"
#include "PGA849.h"
#include "DAC_OUT.h"
#include "CH446Q.h"
#include "DG4052EEQ.h"
#include "AD9833.h"
#include "ADS1219.h"
#include "MCP4725A.h"
#include "PUSE_CAPTURE.h"
#include "MCU_ADC.h"
#include "AAF_IO.h"
#include "DisCharge.h"
#include "FUNC_API.h"

//函数名列表初始化(用户自己添加)
//用户直接在这里输入要执行的函数名及其查找串
struct _m_usmart_nametab usmart_nametab[]=
{
#if USMART_USE_WRFUNS==1 	//如果使能了读写操作
	(void*)read_addr,(u8 *)"u32 read_addr(u32 addr)",
	(void*)write_addr,(u8 *)"void write_addr(u32 addr,u32 val)",	 
#endif		   
	(void*)delay_ms,(u8 *)"void delay_ms(u16 nms)",
 	(void*)delay_us,(u8 *)"void delay_us(u32 nus)",
  (void*)POWER_SET,(u8 *)"void POWER_SET(u8 pow_en,u8 pow_en1,u8 pow_en2,u8 pwren_link)",	
	(void*)POWER_READ,(u8 *)"void POWER_READ(void)",		
  (void*)PGA849_set,(u8 *)"void PGA849_set(u8 vref0or1_25,u8 gain,u8 ADG1409_A0_A1)",
	(void*)CH446Q_MIX_CONTROL,(u8 *)"void CH446Q_MIX_CONTROL(u8 cs,u8 ax,u8 ay,u8 on_off)",
	(void*)CH446Q_Reset,(u8 *)"void CH446Q_Reset(void)",
	(void*)Dac1_Set_Vol,(u8 *)"void Dac1_Set_Vol(u8 L_R,u32 vol)",
	(void*)ADC1_2_Init,(u8 *)"void ADC1_2_Init(u8 simpr,u16 OSVR, u8 OVSS,u8 JOVSE,u8 ROVSE,u32  length)",
	(void*)ADC_BUFFER_READ,(u8 *)"void ADC_BUFFER_READ(u8 model)",
	(void*)ADS1219_init,(u8 *)"void ADS1219_init(u8 mux,u8 gain,u8 dr,u8 cm,u8 vref)",
	(void*)ADS1219_Read_vol,(u8 *)"float ADS1219_Read_vol(void)",	
	(void*)DG4052EEQ_Set,(u8 *)"void DG4052EEQ_Set(u8 set_res)",
  (void*)AD9833_SelectWave,(u8 *)"void AD9833_SelectWave(u8 select)",
  (void*)AD9833_SetFreq,(u8 *)"void AD9833_SetFreq(u32 _freq)",	
  (void*)MCP4725A_Set_Voltage,(u8 *)"void MCP4725A_Set_Voltage(u8 chip_numb,u8 write_mode,u8 out_put_mode,u16 vol_out)",
  (void*)MCP4725A_Set_DAC,(u8 *)"void MCP4725A_Set_DAC(u8 chip_numb,u8 write_mode,u8 out_put_mode,u16 dac_out)",
	(void*)Read_Puse,(u8 *)"float Read_Puse(u8 mode)",			
	(void*)Read_Mcu_ADC,(u8 *)"float Read_Mcu_ADC(u8 ch)",		
	(void*)AAF_set_IO,(u8 *)"void AAF_set_IO(u8 IO_SW3_A0,u8 IO_SW3_A1,u8 IO_SW3_A2,u8 IO_SW4_A0,u8 IO_SW4_A1,u8 IO_SW4_A2)",	
  (void*)DisCharge_Init,(u8 *)"void DisCharge_Init(void)",
	(void*)DisCharge_SET,(u8 *)"void DisCharge_SET(u8 J1_en,u8 J2_en)",	
	(void*)Res_Meas,(u8 *)"void Res_Meas(u8 range,u8 number,u8 mode)",
	(void*)Cap_Meas_sw,(u8 *)"void Cap_Meas_sw(u8 range,u8 number,u8 mode,u16 low,u16 hi)",	
};						  
///////////////////////////////////END///////////////////////////////////////////////
//函数控制管理器初始化
//得到各个受控函数的名字
//得到函数总数量
struct _m_usmart_dev usmart_dev=
{
	usmart_nametab,
	usmart_init,
	usmart_cmd_rec,
	usmart_exe,
	usmart_scan,
	sizeof(usmart_nametab)/sizeof(struct _m_usmart_nametab),//函数数量
	0,	  //参数数量
	0,	 	//函数ID
	1,		//参数显示类型,0,10进制;1,16进制
	0,		//参数类型.bitx:,0,数字;1,字符串	    
	0,	  //每个参数的长度暂存表,需要MAX_PARM个0初始化
	0,		//函数的参数,需要PARM_LEN个0初始化
};   




















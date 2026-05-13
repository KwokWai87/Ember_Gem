#include "FUNC_API.h"


void Res_Meas(u8 range,u8 number,u8 mode)
{
	float vol_average=0.0f,res_ohm=0.0f;
	u8 i=0;
	print_en=mode;
	POWER_SET(1,1,1,0);
	delay_ms(100);
 switch(range)
 {
	 case 0:DG4052EEQ_Set(3);         //10¦¸
		      PGA849_set(1,7,1);
	        Dac1_Set_Vol(1,2500);
		      break;
 	 case 1:DG4052EEQ_Set(2);         //1K
		      PGA849_set(1,3,1);
	        Dac1_Set_Vol(1,2500);
		      break;
	 case 2:DG4052EEQ_Set(1);        //10K
		      PGA849_set(1,3,1);
	        Dac1_Set_Vol(1,2500);
		      break;
	 case 3:DG4052EEQ_Set(1);        //100K
		      PGA849_set(1,3,1);
	        Dac1_Set_Vol(1,235);
		      break;
	 case 4:DG4052EEQ_Set(0);        //1M
		      PGA849_set(1,3,1);
	        Dac1_Set_Vol(1,500);
		      break;
	 case 5:DG4052EEQ_Set(0);        //3M
		      PGA849_set(1,3,1);
					Dac1_Set_Vol(1,200);
		      break;
	 case 6:
		      break;	 
 }
   delay_ms(10); 
   ADS1219_init(0,0,0,0,1);
   delay_ms(20);
   for(i=0;i<number;i++) vol_average+=ADS1219_Read_vol();
   vol_average=vol_average/number;
   POWER_SET(0,0,0,0);
   print_en=1;
  switch(range)
 {
	 case 0:res_ohm=vol_average/10.0f;//10¦¸
		      break;
 	 case 1:res_ohm=vol_average/1.0f;//1K
		      break;
	 case 2:res_ohm=vol_average/0.1f;//10K
		      break;
	 case 3:res_ohm=vol_average/0.01f;//100K
		      break;
	 case 4:res_ohm=vol_average/0.001f;//1M
		      break;
	 case 5:res_ohm=vol_average/0.0004f;//3M
		      break;
	 case 6:
		      break;	 
 }
  sys_print("res_ohm:%0.6f¦¸\r\n",res_ohm);
}

void Cap_Meas(u8 range,u8 number,u8 mode)
{
	float puse_average=0.0f,cap_uF;
	u8 i=0;
	print_en=mode;
	POWER_SET(1,1,1,0);
	delay_ms(100);
	 switch(range)
 {
	 case 0:MCP4725A_Set_Voltage(1,1,0,375);  //10uF
	        MCP4725A_Set_Voltage(2,1,0,875); 
          DG4052EEQ_Set(2);
          Dac1_Set_Vol(1,2500);	 
		      break;
 	 case 1:MCP4725A_Set_Voltage(1,1,0,375); //100uF
	        MCP4725A_Set_Voltage(2,1,0,875);  
	        DG4052EEQ_Set(1);
          Dac1_Set_Vol(1,2500);	 
		      break;
	 case 2: 
		      break;	 
 }
   for(i=0;i<number;i++) puse_average+=Read_Puse(1);
   puse_average=puse_average/number;	
   POWER_SET(0,0,0,0);
   print_en=1;
	 switch(range)
 {
	 case 0:cap_uF=0.1f/(((float)(875.0f-375.0f))/puse_average); //10uF
		      break;
 	 case 1:cap_uF=1.0f/(((float)(875.0f-375.0f))/puse_average); //100uF
		      break;
	 case 2: 
		      break;	 
 } 
 sys_print("cap_uF:%0.6fuF\r\n",cap_uF); 
}

void Cap_Meas_sw(u8 range,u8 number,u8 mode,u16 low,u16 hi)
{
	float puse_average=0,cap_uF=0.0f;
	u8 i=0;
  print_en=mode;
	POWER_SET(1,1,1,0);
	delay_ms(100);
	if(low>3299) low=3299;
	if(hi>3299) hi=3299;
	 switch(range)
 {
	 case 0:MCP4725A_Set_Voltage(1,1,0,low);  //10uF
	        MCP4725A_Set_Voltage(2,1,0,hi); 
          DG4052EEQ_Set(2);
          Dac1_Set_Vol(1,2500);	 
		      break;
 	 case 1:MCP4725A_Set_Voltage(1,1,0,low); //100uF
	        MCP4725A_Set_Voltage(2,1,0,hi);  
	        DG4052EEQ_Set(1);
          Dac1_Set_Vol(1,2500);	 
		      break;
	 case 2: 
		      break;	 
 }
	
   for(i=0;i<number;i++) puse_average+=Read_Puse(1);
   puse_average=puse_average/number;	   	
   POWER_SET(0,0,0,0);
   print_en=1;
	 switch(range)
 {
	 case 0:cap_uF=0.1f/(((float)(hi-low))/puse_average); //10uF
		      break;
 	 case 1:cap_uF=1.0f/(((float)(hi-low))/puse_average); //100uF
		      break;
	 case 2: 
		      break;	 
 } 
 sys_print("cap_uF:%0.6fuF\r\n",cap_uF);
}

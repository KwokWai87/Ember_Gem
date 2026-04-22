#include "MCP4725A.h"


void MCP4725A_init(u8 chip_numb)
{
 u8 temp[5],addr;
 u16 temp16=0;
 float eeprom_voltage=0.0f,DAC_out_voltage=0.0f;
switch(chip_numb)
{
	case 1:addr=MCP4725A_ADDR1;			
				 break;
	case 2:addr=MCP4725A_ADDR2;	
				 break;		
	default: break;
}
 IIC4_Read_direct_bytes(addr,temp,5);
	
 temp16=((temp[3]<<8)|temp[4])&0x0FFF;
 eeprom_voltage=DAC_LSB*(float)temp16;
 printf((char*)"ch%d_eeprom_voltage:%0.4f V\r\n",chip_numb,eeprom_voltage);
	
 temp16=((temp[1]<<8)|temp[2])>>4;
 DAC_out_voltage=DAC_LSB*(float)temp16;
 printf((char*)"ch%d_DAC_out_voltage:%0.4f V\r\n",chip_numb,DAC_out_voltage);	
	
 switch(temp[0]&0x06)
 {
	 case 0x00:printf((char*)"ch%d_normal mode DAC out now\r\n",chip_numb);	
		         break;
	 case 0x02:printf((char*)"ch%d_1KΩ on GND,DAC OFF\r\n",chip_numb);	
		         break;
	 case 0x04:printf((char*)"ch%d_100KΩ on GND,DAC OFF\r\n",chip_numb);	
		         break;
	 case 0x06:printf((char*)"ch%d_500KΩ on GND,DAC OFF\r\n",chip_numb);	
		         break;	 
 }
  switch(temp[0]&0xC0)
 {
	 case 0x00:printf((char*)"ch%d_eeprom busy and suppot vlotage low\r\n",chip_numb);	
		         break;
	 case 0x40:printf((char*)"ch%d_eeprom busy and suppot vlotage ok\r\n",chip_numb);	
		         break;
	 case 0x80:printf((char*)"ch%d_eeprom ready and suppot vlotage low\r\n",chip_numb);	
		         break;
	 case 0xC0:printf((char*)"ch%d_eeprom ready and suppot vlotage ok\r\n",chip_numb);	
		         break;	 
 }
 if((eeprom_voltage!=0.0f)||(DAC_out_voltage!=0.0f))
 {
  printf((char*)"ch%d_set default 0mv\r\n",chip_numb);	
  MCP4725A_Set_Voltage(chip_numb,SAVE,OUT_OFF_500K_TO_GND,0); 
 }
}



//write_mode
//#define SAVE   0
//#define FAST   1
//out_put_mode
//#define OUT_ON                0
//#define OUT_OFF_1K_TO_GND     1
//#define OUT_OFF_100K_TO_GND   2
//#define OUT_OFF_500K_TO_GND   3

void MCP4725A_Set_DAC(u8 chip_numb,u8 write_mode,u8 out_put_mode,u16 dac_out)
{
 u8 temp[7],addr,t=50;
 u16 temp16=0;
switch(chip_numb)
{
	case 1:addr=MCP4725A_ADDR1;			
				 break;
	case 2:addr=MCP4725A_ADDR2;	
				 break;		
	default: break;
}
 switch(write_mode)
 {      
   case FAST:temp[0]=(((u8)(dac_out>>8))&0x0F)|((out_put_mode&0x02)<<4); //快速改变DAC的输出，但不同步EEPROM值
	           temp[1]=(u8)dac_out;
	           while(t--)
						 {
	           IIC4_Write_direct_bytes(addr,temp,2);
	           delay_ms(10);
						 //读取验证
						 IIC4_Read_direct_bytes(addr,&temp[2],5);	
						 temp16=(temp[3]<<8)|temp[4];
						 if(temp16==dac_out)break;
						 }
		         break;
   case SAVE:temp[0]=0x60|((out_put_mode&0x02)<<1); //改变DAC的输出同时同步到EEPROM,速度较慢
	           temp[1]=(u8)(dac_out>>4); 
             temp[2]=(u8)(dac_out<<4);  
	           while(t--)
						 {
             IIC4_Write_direct_bytes(addr,temp,3);	
	           delay_ms(10);
						 //读取验证
						 IIC4_Read_direct_bytes(addr,&temp[2],5);	
						 temp16=(temp[5]<<8)|temp[6];
						 if(temp16==dac_out)break;
						 }						  
		         break;
 }

}
void MCP4725A_Set_Voltage(u8 chip_numb,u8 write_mode,u8 out_put_mode,u16 vol_out)
{
// u8 temp[3],addr;
 u16 DAC_value=0;
 if(vol_out>=3300)DAC_value=0xFFFF;
 else DAC_value=(float)vol_out/1000.0f/DAC_LSB;
	
 MCP4725A_Set_DAC( chip_numb, write_mode, out_put_mode, DAC_value);
}
                                                       //0-5000mA
void Set_Current(u8 chip_numb,u8 write_mode,float current)
{
 float vol_out= 0.0f;	

 if(current<300) vol_out=0;
 else
 {	
 current=current/1000.0f;
 vol_out=current*0.01f/20.0f*1200.0f;
 if(vol_out>=3.3f)vol_out=3.3f;
 }
 MCP4725A_Set_Voltage(chip_numb, write_mode,OUT_ON,vol_out);
}

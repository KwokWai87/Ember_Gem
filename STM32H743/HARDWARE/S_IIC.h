#ifndef __S_IIC_H_
#define __S_IIC_H_


#include "sys.h"
#include "delay.h"

//IO方向设置
#define SDA1_IN()  {GPIOB->MODER&=~((u32)3<<(7*2));GPIOB->MODER|=((u32)0<<(7*2));}	//PB7输入模式
#define SDA1_OUT() {GPIOB->MODER&=~((u32)3<<(7*2));GPIOB->MODER|=((u32)1<<(7*2));} //PB7输出模式
//IO操作函数	 
#define IIC1_SCL(x)		    GPIO_Pin_Set(GPIOB,PIN6,x)		//SCL
#define IIC1_SDA(x)		    GPIO_Pin_Set(GPIOB,PIN7,x)		//SDA
#define READ_SDA1		      GPIO_Pin_Get(GPIOB,PIN7)   		//读取SDA

//IO方向设置
#define SDA4_IN()  {GPIOF->MODER&=~((u32)3<<(15*2));GPIOF->MODER|=((u32)0<<(15*2));}	//PF15输入模式
#define SDA4_OUT() {GPIOF->MODER&=~((u32)3<<(15*2));GPIOF->MODER|=((u32)1<<(15*2));} //PF15输出模式
//IO操作函数	 
#define IIC4_SCL(x)		    GPIO_Pin_Set(GPIOF,PIN14,x)		//SCL
#define IIC4_SDA(x)		    GPIO_Pin_Set(GPIOF,PIN15,x)		//SDA
#define READ_SDA4		      GPIO_Pin_Get(GPIOF,PIN15)   	//读取SDA


void IIC1_Init(void);                //初始化IIC的IO口				 
void IIC1_Start(void);				//发送IIC开始信号
void IIC1_Stop(void);	  			//发送IIC停止信号
void IIC1_Send_Byte(u8 txd);			//IIC发送一个字节
u8 IIC1_Read_Byte(unsigned char ack);//IIC读取一个字节
u8 IIC1_Wait_Ack(void); 				//IIC等待ACK信号
void IIC1_Ack(void);					//IIC发送ACK信号
void IIC1_NAck(void);				//IIC不发送ACK信号

void IIC4_Init(void);                //初始化IIC的IO口				 
void IIC4_Start(void);				//发送IIC开始信号
void IIC4_Stop(void);	  			//发送IIC停止信号
void IIC4_Send_Byte(u8 txd);			//IIC发送一个字节
u8 IIC4_Read_Byte(unsigned char ack);//IIC读取一个字节
u8 IIC4_Wait_Ack(void); 				//IIC等待ACK信号
void IIC4_Ack(void);					//IIC发送ACK信号
void IIC4_NAck(void);				//IIC不发送ACK信号

u8 IIC1_Read_direct_bytes(u8 slaveadd,u8 *pBuffer,u16 NumToRead);
u8 IIC1_ReadOneByte(u8 slaveadd,u16 ReadAddr,u8 double_address);							//指定地址读取一个字节
u8 IIC1_Write_direct_bytes(u8 slaveadd,u8 *pBuffer,u16 NumToWrite);
u8 IIC1_WriteOneByte(u8 slaveadd,u16 WriteAddr,u8 DataToWrite,u8 double_address);		//指定地址写入一个字节
u8 IIC1_Write_Nbytes(u8 slaveadd,u16 WriteAddr,u8 *pBuffer,u16 NumToWrite,u8 double_address);	//从指定地址开始写入指定长度的数据
u8 IIC1_Read_Nbytes(u8 slaveadd,u16 ReadAddr,u8 *pBuffer,u16 NumToRead,u8 double_address);   	//从指定地址开始读出指定长度的数据

u8 IIC4_Read_direct_bytes(u8 slaveadd,u8 *pBuffer,u16 NumToRead);
u8 IIC4_ReadOneByte(u8 slaveadd,u16 ReadAddr,u8 double_address);							//指定地址读取一个字节
u8 IIC4_Write_direct_bytes(u8 slaveadd,u8 *pBuffer,u16 NumToWrite);
u8 IIC4_Write_direct_byte(u8 slaveadd,u8 cmd);
u8 IIC4_WriteOneByte(u8 slaveadd,u16 WriteAddr,u8 DataToWrite,u8 double_address);		//指定地址写入一个字节
u8 IIC4_Write_Nbytes(u8 slaveadd,u16 WriteAddr,u8 *pBuffer,u16 NumToWrite,u8 double_address);	//从指定地址开始写入指定长度的数据
u8 IIC4_Read_Nbytes(u8 slaveadd,u16 ReadAddr,u8 *pBuffer,u16 NumToRead,u8 double_address);   	//从指定地址开始读出指定长度的数据

#endif

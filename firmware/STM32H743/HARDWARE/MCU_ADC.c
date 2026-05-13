#include "MCU_ADC.h"
q15_t ADC_BUFFER[30*1024]__attribute__ ((section("in_sram1_to_3")));
q15_t ADC_BUFFER1[30*1024]__attribute__ ((section("in_sram1_to_3")));
q15_t ADC_BUFFER2[30*1024]SDRAM_AREA_ATTRIBUTE;
float  ADC_VOL[90*1024]SDRAM_AREA_ATTRIBUTE;
u32 ADC_BUFFER_SIZE=30*1024;
// 1. 初始化ADC1为差分模式 (引脚 PA0_C / PA1_C)
void ADC1_2_Init(u8 simpr,u16 OSVR, u8 OVSS,u8 JOVSE,u8 ROVSE,u32  length)
{  	
 /* 1. 时钟 */
    RCC->AHB4ENR |= (1UL << 0);   // GPIOA
    RCC->AHB1ENR |= (1UL << 5);   // ADC12
    RCC->AHB1ENR |= (1UL << 0);   // DMA1
    RCC->APB4ENR |= (1UL << 1);   // SYSCFG
	
    /* 2. GPIO */
    GPIOA->MODER |= (3UL << 0) | (3UL << 2);
    GPIOA->PUPDR &= ~((3UL << 0) | (3UL << 2));

    /* 3. 模拟开关 */
    SYSCFG->PMCR |= (3UL << 24);

    /* 4. ADC 复位 */
    RCC->AHB1RSTR |= (1UL << 5);
    RCC->AHB1RSTR &= ~(1UL << 5);

    /* 5. ADC 时钟 */
    RCC->D3CCIPR &= ~(3UL << 16);
    RCC->D3CCIPR |= (2UL << 16); //per_ck 64M

    ADC12_COMMON->CCR |= (0UL << 18); //64M/2=32M

    /* 6. 唤醒 */
    ADC1->CR &= ~(1UL << 29);
    ADC1->CR |= (1UL << 28);

     delay_ms(10);
    /* 7. BOOST */
    ADC1->CR |= (1UL << 8);

    /* 8. 差分 */
    ADC1->DIFSEL |= (1UL << 1);
    ADC1->PCSEL |= (1UL << 1) | (1UL << 0);

    /* 9. 分辨率 */
    ADC1->CFGR &= ~(7UL << 2);

    if((JOVSE==1)||(ROVSE==1))
		{
		if(OSVR>1023)	
		{ 
			sys_print("OSVR err,should be 0~1023,set to 0\r\n");
			OSVR=0;
		}
		if(OVSS>11)	
		{ 
			sys_print("OVSS err,should be 0~11,set to 0\r\n");
		}	
		if(JOVSE>1)	
		{ 
			sys_print("JOVSE err,should be 0~1,set to 0\r\n");
		}
		if(ROVSE>1)	
		{ 
			sys_print("ROVSE err,should be 0~1,set to 0\r\n");
		}		    		
    ADC1->CFGR2 =0;
		ADC1->CFGR2 |=((u32)OSVR << 16)|((u32)OVSS << 5)| ((u32)JOVSE << 1)| ((u32)ROVSE << 0);
		sys_print("OSVR:%d\r\n",OSVR);	
    sys_print("OVSS:%d\r\n",OVSS);		
		sys_print("JOVSE:%d\r\n",JOVSE);	
    sys_print("ROVSE:%d\r\n",ROVSE);				
		}

    /*10. 关键：DMA + 连续模式 */
    ADC1->CFGR |= (1UL << 13);   // CONT = 1
    ADC1->CFGR |= (1UL << 0);    // DMAEN = 1
    ADC1->CFGR |= (1UL << 1);    // DMACFG = 1 (循环)

  if(length>30720)
	{
	 length=30720;
	 sys_print("ADC_buffer<=30KB\r\n");
	}
	
	ADC_BUFFER_SIZE=length;
	sys_print("ADC_BUFFER_SIZE:%d\r\n",length);
	switch(simpr)
	{
		case 0:sys_print("1.5 ADC clock cycles(default)\r\n"); 
		       break;
		case 1:sys_print("2.5 ADC clock cycles\r\n"); 
		       break;	
		case 2:sys_print("8.5 ADC clock cycles\r\n"); 
		       break;	
		case 3:sys_print("16.5 ADC clock cycles\r\n"); 
		       break;	
		case 4:sys_print("32.5 ADC clock cycles\r\n"); 
		       break;
		case 5:sys_print("64.5 ADC clock cycles\r\n"); 
		       break;
		case 6:sys_print("327.5 ADC clock cycles\r\n"); 
		       break;
		case 7:sys_print("810.5 ADC clock cycles\r\n"); 
		       break;
		default:simpr=0;
			     sys_print("simpr err! should be 0~7,set to 0 now!\r\n");
           break;	
	}
    /* 15. 采样时间（CH1） */
    ADC1->SMPR1 &= ~(7UL << 3);
    ADC1->SMPR1 |= ((u32)simpr << 3);   // 64.5 cycles（推荐）
    /* 11. 序列 */
    ADC1->SQR1 &= ~(0x1F << 6);
    ADC1->SQR1 |= (1UL << 6);

		/* 12. 进阶高精度校准 (偏移校准 + 线性校准) */
		ADC1->CR |= (1UL << 30);  // ADCALDIF = 1 (差分输入模式校准)
		ADC1->CR |= (1UL << 16);  // ADCALLIN = 1 (开启线性校准，极大改善 INL)

		ADC1->CR |= (1UL << 31);  // ADCAL = 1 (正式启动校准)
		while (ADC1->CR & (1UL << 31)){}; // 等待校准完成

	/* =========================
		 DMA 配置（DMA1 Stream0）
		 ========================= */
	DMA1_Stream1->CR &= ~1;
	while (DMA1_Stream1->CR & 1){};
	// 配置 DMAMUX：ADC1 → DMA1_Stream0
	DMA1->LIFCR|=0X3D<<6*1;		//清空之前该stream上的所有中断标志	
	DMAMUX1_Channel1->CCR = 9;   // ADC1 request ID = 9
	DMA1_Stream1->PAR  = (uint32_t)&ADC1->DR;
	DMA1_Stream1->M0AR = (uint32_t)ADC_BUFFER;
	DMA1_Stream1->NDTR = (uint32_t)length;
	DMA1_Stream1->CR=0;
	DMA1_Stream1->CR =
			(3 << 15) |   //Very high
			(1 << 10) |   // 内存自增
			(0 << 9)  |   // 外设不增
			(0 << 8)  |   // 循环模式
			(0 << 6)  |   // 外设->内存
			(1 << 13) |   // 内存16bit
			(1 << 11) |    // 外设16bit
		  (1 << 23) |   //内存突发单次传输
      (1 << 21);    //外设突发单次传输
//    DMA1->LIFCR = 0xFFFFFFFF;
	DMA1_Stream1->CR |= 1; // 使能 DMA

    /* 13. 使能 ADC */
    ADC1->ISR |= 1;
    ADC1->CR |= 1;
    while (!(ADC1->ISR & 1));

    /* 14. 启动转换 */
    ADC1->CR |= (1UL << 2);
		
		arm_fill_q15(32767,ADC_BUFFER1,ADC_BUFFER_SIZE);
		arm_fill_f32(2.5f,&ADC_VOL[30720],ADC_BUFFER_SIZE);
}

// 2. 获取单次原始值 (工业级带超时防护)
// 返回值：保留原 u32 类型兼容上层代码，但低 16 位实为【有符号补码】
u16 Get_Adc(u8 ch)   
{
    // 【删除这行】ADC1->PCSEL |= (1UL<<ch); // 运行时写不进去，必须删掉！
		 
    ADC1->SQR1 &= ~(0x1FUL << 6);	// 清除 SQ1
    ADC1->SQR1 |= ((u32)ch << 6);	// 写入通道号 (差分下始终传入1
    ADC1->SQR1 &= ~(0xFUL << 0);    // 序列长度为1次转换

    ADC1->ISR |= (1UL << 2);        // 清空 EOC 标志位
    ADC1->CR |= (1UL << 2);       	// 启动转换 (ADSTART)
    
    uint32_t timeout = 0xFFFFF;
    while(!(ADC1->ISR & (1UL << 2)) && timeout) 
    {
        timeout--;
    }
    
    return ADC1->DR;			    // 返回真实结果
}

// 3. 求平均算法 (纯无符号处理，彻底消除 #68-D 警告)
u32 Get_Adc_Average(u8 ch, u8 times)
{
    u32 temp_val = 0; 
    u8 t;
    for(t = 0; t < times; t++)
    {
        // 直接累加 0~65535 的无符号原始值
        temp_val += Get_Adc(ch); 
        delay_ms(5); 
    }
    return (temp_val / times); 
}  

float Read_Mcu_ADC(u8 ch)
{
    u32 temp_avg = 0;
    int32_t true_diff = 0;
    float vol = 0.0f;  
    // 【核心修正】：必须读取通道 1 (Channel 1 才是真正的 PA1_C / PA0_C 差分对)
    temp_avg = Get_Adc_Average(1, 20);

    // 偏移二进制解码：减去半量程 32768
    true_diff = (int32_t)temp_avg - 32768; 

    // 数学转换
    vol = (float)true_diff * (2.5f / 32768.0f);
    
    sys_print("MCU_ADC_vol:%0.4f V\r\n", vol);
    sys_print("MCU_ADC_raw:%u, true_diff:%d\r\n", temp_avg, true_diff); 
	  return vol;
}

void ADC_BUFFER_READ(u8 model)
{
	u32 i=0,MAX_INDEX=0,MIN_INDEX=0;
	int32_t true_diff = 0;
	float vol = 0.0f,max_vol,min_vol,Vpp,Rms;
	
	if(model==2)
 {
 for(i=0;i<ADC_BUFFER_SIZE;i++)sys_print("%d,", ADC_BUFFER[i]);
 sys_print("\r\n" );
 }
 else if(model==1)
{
	for(i=0;i<ADC_BUFFER_SIZE;i++)
 {
		true_diff =(u16)ADC_BUFFER[i] - 32768;
    vol = (float)true_diff * (2.5f / 32768.0f);	
   // ADC_VOL[i]=vol;	 
    sys_print("%0.4f,", vol);
 }
	 sys_print("\r\n");

}
else
{  
		DMA1_Stream1->CR &= ~1;
		while (DMA1_Stream1->CR & 1){};
		DMA1_Stream1->NDTR =ADC_BUFFER_SIZE;
		DMA1_Stream1->CR |= 1; // 使能 DMA
		/* 14. 启动转换 */
		ADC1->ISR |= (1UL << 2);        // 清空 EOC 标志位
		ADC1->CR |= (1UL << 2);       	// 启动转换 (ADSTART)		
		while (!(DMA1->LISR & DMA_LISR_TCIF1)){};
		DMA1->LIFCR = DMA_LIFCR_CTCIF1;	
		arm_add_q15(ADC_BUFFER,ADC_BUFFER1,ADC_BUFFER2,ADC_BUFFER_SIZE);
		arm_q15_to_float(ADC_BUFFER2,&ADC_VOL[61440],ADC_BUFFER_SIZE);
		arm_mult_f32(&ADC_VOL[30720],&ADC_VOL[61440],ADC_VOL,ADC_BUFFER_SIZE);	
		arm_max_f32(ADC_VOL,ADC_BUFFER_SIZE,&max_vol,&MAX_INDEX);
		arm_min_f32(ADC_VOL,ADC_BUFFER_SIZE,&min_vol,&MIN_INDEX);
		arm_rms_f32(ADC_VOL,ADC_BUFFER_SIZE,&Rms);
		Vpp=max_vol-min_vol;
		sys_print("Vpp:%0.4f,Rms:%0.4f\r\n",Vpp,Rms);
}

SCB_InvalidateDCache_by_Addr((uint32_t*)ADC_BUFFER, ADC_BUFFER_SIZE);
//SCB_InvalidateDCache_by_Addr((uint32_t*)ADC_VOL, ADC_BUFFER_SIZE);

}
//DMAx的各通道配置
//这里的传输形式是固定的,这点要根据不同的情况来修改
//从存储器->外设模式/8位数据宽度/存储器增量模式
//DMA_Streamx:DMA数据流,DMA1_Stream0~7/DMA2_Stream0~7
//chx:DMA通道选择,范围:1~115(详见<<STM32H7xx参考手册>>16.3.2节,Table 116)
//par:外设地址
//mar:存储器地址
//ndtr:数据传输量  
void MYDMA_Config(DMA_Stream_TypeDef *DMA_Streamx,u8 chx,u32 par,u32 mar,u16 ndtr,u8 model,u8 dir)
{ 
	DMA_TypeDef *DMAx;
	DMAMUX_Channel_TypeDef *DMAMUXx;
	u8 streamx;
	if((u32)DMA_Streamx>(u32)DMA2)//得到当前stream是属于DMA2还是DMA1
	{
		DMAx=DMA2;
		RCC->AHB1ENR|=1<<1;		//DMA2时钟使能  
	}else 
	{
		DMAx=DMA1; 
 		RCC->AHB1ENR|=1<<0;		//DMA1时钟使能 
	}
	DMA_Streamx->CR&=~(1<<0); 	//关闭DMA传输	
	while(DMA_Streamx->CR&0x01);//等待DMA可配置 
	streamx=(((u32)DMA_Streamx-(u32)DMAx)-0X10)/0X18;			//得到stream通道号
 	if(streamx>=6)DMAx->HIFCR|=0X3D<<(6*(streamx-6)+16);		//清空之前该stream上的所有中断标志
	else if(streamx>=4)DMAx->HIFCR|=0X3D<<6*(streamx-4);		//清空之前该stream上的所有中断标志
	else if(streamx>=2)DMAx->LIFCR|=0X3D<<(6*(streamx-2)+16);	//清空之前该stream上的所有中断标志
	else DMAx->LIFCR|=0X3D<<6*streamx;							//清空之前该stream上的所有中断标志

	if((u32)DMA_Streamx>(u32)DMA2)streamx+=8;					//如果是DMA2,通道编号+8 
	DMAMUXx=(DMAMUX_Channel_TypeDef *)(DMAMUX1_BASE+streamx*4);	//得到对应的DMAMUX通道控制地址
	DMAMUXx->CCR=chx&0XFF;		//通道选择
	
	DMA_Streamx->PAR=par;		//DMA外设地址
	DMA_Streamx->M0AR=mar;		//DMA 存储器0地址
	DMA_Streamx->NDTR=ndtr;		//传输数据长度
	DMA_Streamx->CR=0;			//先全部复位CR寄存器值 
	
	if(dir==1)DMA_Streamx->CR&=~(1<<6); //外设到存储器模式		
	else DMA_Streamx->CR|=1<<6;      //存储器到外设模式    
	if(model==1)DMA_Streamx->CR&=~(1<<8);		//非循环模式(即使用普通模式)
	else DMA_Streamx->CR|=1<<8;         //循环模式
	DMA_Streamx->CR|=0<<9;		//外设非增量模式
	DMA_Streamx->CR|=1<<10;		//存储器增量模式
	DMA_Streamx->CR|=1<<11;		//外设数据长度:16位
	DMA_Streamx->CR|=1<<13;		//存储器数据长度:16位
	DMA_Streamx->CR|=3<<16;		//中等优先级
	DMA_Streamx->CR|=0<<21;		//外设突发单次传输
	DMA_Streamx->CR|=0<<23;		//存储器突发单次传输
	 
	//DMA_Streamx->FCR=0X21;	//FIFO控制寄存器 
 	DMA_Streamx->CR|=1<<0;		//开启DMA传输	
}

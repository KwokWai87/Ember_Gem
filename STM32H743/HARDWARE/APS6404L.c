#include "APS6404L.h"

u8 APS6404L_buffer[5]={0x00,0x01,0x02,0x03,0x04};
u8 APS6404L_buffer1[5];
void APS6404L_Init(void)
{
	QSPI_Init();					//初始化QSPI
	
  QUADSPI->CR = 0;
QUADSPI->DCR = 0;

// Prescaler = 2 → 100MHz/2 = 50MHz（保守）
QUADSPI->CR |= (1 << QUADSPI_CR_PRESCALER_Pos);

// FIFO threshold
QUADSPI->CR |= (3 << QUADSPI_CR_FTHRES_Pos);

// Flash size = 8MB → 2^23
QUADSPI->DCR |= (22 << QUADSPI_DCR_FSIZE_Pos);

// CS 高电平时间
QUADSPI->DCR |= (2 << QUADSPI_DCR_CSHT_Pos);

// 使能
QUADSPI->CR |= QUADSPI_CR_EN;

    // Reset
    QSPI_Cmd1Line(0x66);
    QSPI_Cmd1Line(0x99);
	delay_ms(1000); // 复位需要等待一段时间 (tRST)

//	// 3. 进入 QPI 模式 (0x35)
//	// 此时芯片已复位到标准 SPI 模式，用 1-Line 发送 0x35
//	 QSPI_Cmd1Line(0x35);
	delay_ms(100);
	
 	OSPI_Write_Quad(0,APS6404L_buffer,5);
  OSPI_Read_Quad(0,APS6404L_buffer1,5);
}


// 函数：向 APS6404L 写入数据
// addr: 24位地址, pData: 数据指针, size: 数据长度
void OSPI_Write_Quad(uint32_t addr, uint8_t *pData, uint16_t size)
	{
  QSPI_Wait();

    QUADSPI->DLR = size - 1;

    QUADSPI->CCR =
        (3 << QUADSPI_CCR_IMODE_Pos) |
        (3 << QUADSPI_CCR_ADMODE_Pos) |
        (3 << QUADSPI_CCR_DMODE_Pos) |
        (0x02 << QUADSPI_CCR_INSTRUCTION_Pos);

    QUADSPI->AR = addr;

    for (uint32_t i = 0; i < size; i++)
    {
        while (!(QUADSPI->SR & QUADSPI_SR_FTF));
        *((volatile uint8_t*)&QUADSPI->DR) = pData[i];
    }

    QSPI_Wait();
    // 实际工程中建议轮询状态寄存器直到 BUSY 位清除
}
	
// 函数：从 APS6404L 读取数据
void OSPI_Read_Quad(uint32_t addr, uint8_t *pData, uint16_t size) 
	{
   QSPI_Wait();

    // 数据长度
    QUADSPI->DLR = size - 1;

    // 配置命令
    QUADSPI->CCR =
        (3 << QUADSPI_CCR_IMODE_Pos) |   // 4-line instruction
        (3 << QUADSPI_CCR_ADMODE_Pos) |  // 4-line address
        (3 << QUADSPI_CCR_DMODE_Pos) |   // 4-line data
        (6 << QUADSPI_CCR_DCYC_Pos)  |   // dummy cycles（关键）
        (0x03 << QUADSPI_CCR_INSTRUCTION_Pos);

    // 地址
    QUADSPI->AR = addr;

    // 读取数据
    for (uint32_t i = 0; i < size; i++)
    {
        while (!(QUADSPI->SR & QUADSPI_SR_FTF));
        pData[i] = *((volatile uint8_t*)&QUADSPI->DR);
    }

    QSPI_Wait();
}
 void QSPI_Wait(void)
{
    while (QUADSPI->SR & QUADSPI_SR_BUSY);
}

void QSPI_Cmd1Line(uint8_t cmd)
{
    QSPI_Wait();

    QUADSPI->CCR =
        (1 << QUADSPI_CCR_IMODE_Pos) |
        (cmd << QUADSPI_CCR_INSTRUCTION_Pos);

    QSPI_Wait();
}

void QSPI_SendCmd(uint8_t instr)
{
    QSPI_Wait();

    QUADSPI->CCR =
        (1 << QUADSPI_CCR_IMODE_Pos) |   // 1-line instruction
        (instr << QUADSPI_CCR_INSTRUCTION_Pos);

    QSPI_Wait();
}

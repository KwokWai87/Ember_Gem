#ifndef __FUNC_API_H
#define __FUNC_API_H

#include "sys.h" 
#include "PGA849.h"
#include "ADS1219.h"
#include "POWER_IO.h"
#include "DG4052EEQ.h"
#include "DAC_OUT.h"
#include "MCP4725A.h"
#include "PUSE_CAPTURE.h"

void Res_Meas(u8 range,u8 number,u8 mode);
void Cap_Meas(u8 range,u8 number,u8 mode);
void Cap_Meas_sw(u8 range,u8 number,u8 mode,u16 low,u16 hi);


#endif

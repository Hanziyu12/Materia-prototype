
#include <DS18B20.h>

#include <SPI.h>
#include <SD.h>
#include <TFT_22_ILI9225.h> 

#include <Wire.h>
#include <TimeLib.h>
#include <DS1307RTC.h>

// Pin definitions for UNO
#define CS   9   // Chip Select
#define RS   2    // Data/Command
#define RST  -1   // No reset pin (tied to Arduino RESET or VCC)
#define LED  -1

// for Doc...()
const char Filename[] = "DataSoC3.txt";

TFT_22_ILI9225 tft = TFT_22_ILI9225(RST, RS, CS, LED, 50);

tmElements_t tm;

const int SDchipSelect = 10; // SD Pin 
/*
   SD card attached to SPI bus as fo  llows:
 ** MOSI - pin 11
 ** MISO - pin 12
 ** CLK - pin 13
 ** CS - pin 10 (for MKRZero SD: SDCARD_SS_PIN)
 */

File SDentry;



//other variables

unsigned long Timer;
unsigned long DocEvent;

// Temperature sensors acting out of a0-a3 (14-17)
DS18B20 Red0(14); // inside organ - turns on pumps
float Red0Temp; //organ
DS18B20 Orange1(15); // organ bag
float Orange1Temp; // organ bag
DS18B20 Yellow2(16); // pcm box
float Yellow2Temp; // pcm box
DS18B20 Green3(17); // outside
float Green3Temp; //outside

int PumpState = -1;
int SwState = -1;

void setup() {
  Serial.begin(9600);
  SD.begin(SDchipSelect);// begining SD card at the chipselect pin

  Red0.setResolution(10);
  Orange1.setResolution(10);
  Yellow2.setResolution(10);
  Green3.setResolution(10);// initialise switch and temp sensors

  tft.begin();

  tft.setOrientation(2);
  tft.setFont(Terminal12x16);
  tft.drawText(0,0, "Organ");
  tft.drawText(100, 0, "Bag");
  tft.drawText(0,75, "Ice");
  tft.drawText(100,75, "Outside");
  tft.drawText(0, 175, "SoC", COLOR_ORANGE);
}

void print2digits(int number) {
  if (number >= 0 && number < 10) {
    Serial.write('0');
    SDentry.print("0");

  }
  Serial.print(number);
  SDentry.print(number);
}

void DocPeriodic(){
  RTC.read(tm);
  SDentry = SD.open(Filename, FILE_WRITE); // change name for different eskies (2 0f 2)
  
  // Date
    Serial.print(tm.Day);
    SDentry.print(tm.Day);
    Serial.write('/');
    SDentry.write('/');
    Serial.print(tm.Month);
    SDentry.print(tm.Month);
    Serial.write('/');
    SDentry.write('/');
    Serial.print(tmYearToCalendar(tm.Year));
    SDentry.print(tmYearToCalendar(tm.Year));
    Serial.print(",");
    SDentry.print(",");

  //  TIME
    print2digits(tm.Hour);
    Serial.write(':');
    SDentry.print(":");
    print2digits(tm.Minute);
    Serial.write(':');
    SDentry.print(":");
    print2digits(tm.Second);
    Serial.print(",");
    SDentry.print(",");
  
  Serial.print("Periodic");
  SDentry.print("Periodic");
  Serial.print(",");
  SDentry.print(",");
  Serial.print(Timer);
  SDentry.print(Timer);
  Serial.print(",");
  SDentry.print(",");
  Serial.print(PumpState);
  SDentry.print(PumpState);
  Serial.print(",");
  SDentry.print(",");
  Serial.print(SwState);
  SDentry.print(SwState);
  Serial.print(",");
  SDentry.print(",");
  Serial.print(Red0Temp);
  SDentry.print(Red0Temp);
  Serial.print(",");
  SDentry.print(",");
  Serial.print(Orange1Temp);
  SDentry.print(Orange1Temp);
  Serial.print(",");
  SDentry.print(",");
  Serial.print(Yellow2Temp);
  SDentry.print(Yellow2Temp);
  Serial.print(",");
  SDentry.print(",");
  Serial.print(Green3Temp);
  SDentry.print(Green3Temp); 
  Serial.println();
  SDentry.println();
  SDentry.close();  // File closed
}

void loop() {

  delay(2000);
  Red0Temp = Red0.getTempC();
  Orange1Temp = Orange1.getTempC();
  Yellow2Temp = Yellow2.getTempC();
  Green3Temp = Green3.getTempC();
  timer();
  
  tft.drawText(0,25, String(Red0Temp, 2)); //organ
  tft.drawText(100,25, String(Orange1Temp, 2)); //organ bag
  tft.drawText(0,100, String(Yellow2Temp, 2)); //pcm
  tft.drawText(100,100, String(Green3Temp, 2));//outside
 
}

void timer(){

  Timer = millis();
  DocEvent=Timer;
  Red0Temp = Red0.getTempC();
  Orange1Temp = Orange1.getTempC();
  Yellow2Temp = Yellow2.getTempC();
  Green3Temp = Green3.getTempC();
  DocPeriodic();

}

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

TFT_22_ILI9225 tft = TFT_22_ILI9225(RST, RS, CS, LED, 50);

tmElements_t tm;

const int SDchipSelect = 10; // SD Pin 
/*
   SD card attached to SPI bus as follows:
 ** MOSI - pin 11
 ** MISO - pin 12
 ** CLK - pin 13
 ** CS - pin 10 (for MKRZero SD: SDCARD_SS_PIN)
 */

File SDentry;

// max and min temperatures in cooling and warming modes 
float LowestCoolTemp = 5;
float HighestCoolTemp = 7;
float LowestRewarmTemp = 35.5;
float HighestRewarmTemp = 37.0; 

// variables for pumpControl()
int PumpState = 0;
int Mode = 1;
int SwState;

// set pump direction and velocity, for changePumpSpeed()
const int PumpDirM1 = 4;  //Fwd- LOW
const int PumpDirM3 = 8;  //Fwd- LOW
const int PumpVelM1 = 3;
const int PumpVelM3 = 5;

// for Doc...()
const char Filename[] = "Datalog1.txt";

//other variables
const int switchPins[2] = {6, 7}; //6 is unused, 7 is cold/rewarming
int switchStates[2];
unsigned long Timer;
unsigned long Event; 
unsigned long PumpEvent; 
int pastfail = 0;

// Temperature sensors acting out of a0-a3 (14-17)
DS18B20 Red0(14); // inside organ - turns on pumps
float Red0Temp; //organ
DS18B20 Orange1(15); // organ bag
float Orange1Temp; // organ bag
DS18B20 Yellow2(16); // pcm box
float Yellow2Temp; // pcm box
DS18B20 Green3(17); // outside
float Green3Temp; //outside

time_t warmStart = 0;
int rewarm; 

void setup() {
  Serial.begin(9600);
  SD.begin(SDchipSelect);// begining SD card at the chipselect pin

  digitalWrite(PumpDirM1, LOW);
  digitalWrite(PumpDirM3, LOW);//set pump direction

  for (int i = 0; i < 2; i++) {
    pinMode(switchPins[i], INPUT);
  }
  Red0.setResolution(10);
  Orange1.setResolution(10);
  Yellow2.setResolution(10);
  Green3.setResolution(10);// initialise switch and temp sensors

  tft.begin();

  tft.setOrientation(3);
  tft.setBacklight(LOW);
  tft.setFont(Terminal12x16);
  tft.drawText(0,0, "Organ");
  tft.drawText(110, 0, "Organ Bag");
  tft.drawText(0,50, "PCM");
  tft.drawText(110,50, "Outside");
  tft.drawText(0, 125, "Pump Status:");
  tft.drawText(0, 150, "Mode:");
}

void print2digits(int number) {
  if (number >= 0 && number < 10) {
    Serial.write('0');
    SDentry.print("0");

  }
  Serial.print(number);
  SDentry.print(number);
}

void DocPumpEvent(){
  RTC.read(tm);
  SDentry = SD.open(Filename, FILE_WRITE); 
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
  Serial.print("PumpEvent");
  SDentry.print("PumpEvent");
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
  checkFailure();
  timer();
  
  String SwMode;
  String PuMode;
  String Lo;
  String Hi;

  if (switchStates[1] == HIGH) {
    SwMode = "WARM";
    Lo = String(LowestRewarmTemp, 1);
    Hi = String(HighestRewarmTemp, 1);
    if (warmStart + 60 < now()) {
      warmStart = now();      // store the start time of warming
      rewarm = Red0Temp + 0.5;    
    } 
  } else {
    SwMode = "COOL";
    Lo = String(LowestCoolTemp, 1);
    Hi = String(HighestCoolTemp, 1);
  }
  if (PumpState == 0){
    PuMode = "OFF";
  } else{
    PuMode = "ON  ";
  }
 
  tft.setFont(Terminal12x16);

  tft.drawText(0,25, String(Red0Temp, 2)); //organ
  tft.drawText(110,25, String(Orange1Temp, 2)); //organ bag
  tft.drawText(0,75, String(Yellow2Temp, 2)); //pcm
  tft.drawText(110,75, String(Green3Temp, 2));//outside
  tft.drawText(140, 125, PuMode); //pump status
  tft.drawText(65, 150, SwMode); //mode
  tft.fillRectangle(tft.maxX()-26, 150, tft.maxX(), tft.maxY(), COLOR_BLACK);
  tft.drawText(115, 150, Lo + '-' + Hi);
}

void pumpControl (int failure) {
  
  float MidTemp;
  float ExTemp;

  if (switchStates[1] == HIGH) {
    //rewarming mode activated
    Mode = -1;
    MidTemp = LowestRewarmTemp*Mode;
    ExTemp = HighestRewarmTemp*Mode;
    SwState = 1;
  } else{
    // cooling mode
    Mode = 1;
    MidTemp = HighestCoolTemp;
    ExTemp = LowestCoolTemp;
    SwState = 0;
  }

//first hour clause - within first hour
  if (Timer < 3600000){
    if ( (PumpState == 0) && (Orange1Temp > (Yellow2Temp+1)) && (Orange1Temp>4) ){
      changePumpSpeed(128);
      return;
    } else if ( (PumpState!=0) && (Orange1Temp <= 4) && (Orange1Temp > (Yellow2Temp+1)) ){
      changePumpSpeed(0);
      return;
    }
  }

  // first hour clause - after the first hour
  if (Timer >= 3600000){
    //if organ container is warm and pcm cooler 
    if (PumpState==0){
      if ( (Orange1Temp*Mode > (Yellow2Temp+1)*Mode) && (Orange1Temp*Mode >= MidTemp ) && (failure == 0) ){ 
        // turn on if organ container more ambient than pcm and at mid allowable temp 
        // there must be a 1 degree differential for it to be worth turning on the pump
        changePumpSpeed(128);
        return;
      } else if ( (failure == 1) && (Red0Temp*Mode > Orange1Temp*Mode) ){ 
        //if pcm sensor failed, assume pcm not wasted
        changePumpSpeed(128);
        return;
      }
    }
 
   if (PumpState!=0){//if pump is on, turn off if
     if (failure >= 3) { 
        //if organ sensor failed and/or both the pcm and organ bag
        changePumpSpeed(0);
        return;
     } else if (Orange1Temp*Mode <= ExTemp) { 
        changePumpSpeed(0);
        return;
     } else if ((Orange1Temp*Mode <= (Yellow2Temp+1)*Mode) && (failure == 0)){ 
       //OR if organ bag equal to or more ideal than pcm, and they arent failures
        changePumpSpeed(0);
        return;
      }

    }
  }

}

void changePumpSpeed (int PumpSpeed){
  
  Event = millis();
  if ((Event-PumpEvent)>=0){
    PumpState = PumpSpeed;
    digitalWrite(PumpVelM1, PumpSpeed);
    digitalWrite(PumpVelM3, PumpSpeed);
    Green3Temp = Green3.getTempC();
    PumpEvent = Event;
    DocPumpEvent();
  }
}

void timer(){

  Timer = millis();
  Red0Temp = Red0.getTempC();
  Orange1Temp = Orange1.getTempC();
  Yellow2Temp = Yellow2.getTempC();
  Green3Temp = Green3.getTempC();
  DocPeriodic();
  switchStates[1] = digitalRead(switchPins[1]);
 
}

void checkFailure() { 
  //failure must occur twice in a row to be valid

  int Temps[] = {Red0Temp, Orange1Temp, Yellow2Temp};
  int check = 0;

  for (int x = 0; x < 3; x++) {
    if ( (Temps[x]==-0.06) || (abs(Temps[x]) > 100) ){
      //assign to a failure code
      check += pow(2, 2-x);
    }
  }

  if (check == 0) {
    //no fail
    pumpControl(check);
    pastfail = check;
    return;  
  } else if (check >= 4 && pastfail >= 4) {
    //failure of organ sensor, turn pump off
    pumpControl(check);
    pastfail = check;
    return;    
  } else if ( (check == 1) && (pastfail & 1) ){
    //failure of pcm 
    pumpControl(check);
    pastfail = check;
    return;    
  } else if ( (check == 2) && (pastfail >= 2) ){
    //failure of organ bag sensor
    pumpControl(check);
    pastfail = check;
    return;
  } else if ( (check == 3) && (pastfail == 3) ){
    //failure of organ bag & pcm sensors
    pumpControl(check);
    pastfail = check;
    return;
  } else {
    pumpControl(pastfail);
    pastfail = check;
  }
}
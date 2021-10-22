/*********
  Rui Santos
  Complete project details at https://RandomNerdTutorials.com/esp32-hc-sr04-ultrasonic-arduino/
  
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files.
  
  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
*********/

const int trigPin1 = 13;
const int echoPin1 = 12;
const int trigPin2 = 14;
const int echoPin2 = 27;
const int trigPin3 = 26;
const int echoPin3 = 25;
const int trigPin4 = 33;
const int echoPin4 = 32;
const int trigPin5 = 5;
const int echoPin5 = 18;

//define sound speed in cm/uS
#define SOUND_SPEED 0.034

long duration1;
long duration2;
long duration3;
long duration4;
long duration5;
float distanceCm1;
float distanceCm2;
float distanceCm3;
float distanceCm4;
float distanceCm5;

void setup() {
  Serial.begin(9600); // Starts the serial communication
  pinMode(trigPin1, OUTPUT); // Sets the trigPin as an Output
  pinMode(trigPin2, OUTPUT); // Sets the trigPin as an Output
  pinMode(trigPin3, OUTPUT); // Sets the trigPin as an Output
  pinMode(trigPin4, OUTPUT); // Sets the trigPin as an Output
  pinMode(trigPin5, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin1, INPUT); // Sets the echoPin as an Input
  pinMode(echoPin2, INPUT); // Sets the echoPin as an Input
  pinMode(echoPin3, INPUT); // Sets the echoPin as an Input
  pinMode(echoPin4, INPUT); // Sets the echoPin as an Input
  pinMode(echoPin5, INPUT); // Sets the echoPin as an Input
}

void loop() {
  // SENSOR 1
  // Clears the trigPin
  digitalWrite(trigPin1, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin1, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin1, LOW);
  
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration1 = pulseIn(echoPin1, HIGH);
  
  // SENSOR 2
  // Clears the trigPin
  digitalWrite(trigPin2, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin2, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin2, LOW);
  
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration2 = pulseIn(echoPin2, HIGH);

  // SENSOR 3
  // Clears the trigPin
  digitalWrite(trigPin3, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin3, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin3, LOW);
  
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration3 = pulseIn(echoPin3, HIGH);

  // SENSOR 4
  // Clears the trigPin
  digitalWrite(trigPin4, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin4, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin4, LOW);
  
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration4 = pulseIn(echoPin4, HIGH);

  // SENSOR 5
  // Clears the trigPin
  digitalWrite(trigPin5, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin5, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin5, LOW);
  
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration5 = pulseIn(echoPin5, HIGH);

  // Calculate the distance
  distanceCm1 = duration1 * SOUND_SPEED/2;
  distanceCm2 = duration2 * SOUND_SPEED/2;
  distanceCm3 = duration3 * SOUND_SPEED/2;
  distanceCm4 = duration4 * SOUND_SPEED/2;
  distanceCm5 = duration5 * SOUND_SPEED/2;
  
  Serial.print(min(float(distanceCm1), float(30)));
  Serial.print(" ");
  Serial.print(min(float(distanceCm2), float(30)));
  Serial.print(" ");
  Serial.print(min(float(distanceCm3), float(30)));
  Serial.print(" ");
  Serial.print(min(float(distanceCm4), float(30)));
  Serial.print(" ");
  Serial.println(min(float(distanceCm5), float(30)));
  
  delay(200);
}

# Microcontroller-based stepper motor control for adhesive force tester
Last verified: 2023-05-04
Last updated: 2023-10-20

## Setting up Pico microcontroller
Left switch uses pin 20 on the microcontroller and is set up with: `lSwitch.setup(20,0,5,0.5)`

Right switch uses pin 18 on the microcontroller and is set up with: `rSwitch.setup(18,step_limit_guess,5,0.5)`

Motor object is set up with: `m.setup([13,12],CCW,100,-6,step_limit_guess)`

## Connecting Pico microcontroller

### Hardware

Plug Pico in to computer via microUSB. Plug microstep driver into power via barrel jack.

### Software
Note: terminal should have (base) in front. To switch to research environment, use `conda activate research`, then the terminal should have (research) in front. If this doesn't work, execution policy may need to be updated, or you may need to use Python: Select Interpreter in the command palette to select the conda Python interpreter.

1. Navigate to the directory containing code for the Pico; i.e., to `C:\Users\Hattongroup\Documents\Code\hattonlab\equipment_and_apparatus\force_tester\software\Pico\` (or the equivalent directory on your device)
2. Run motor setup code using the ampy CLI tool as: `ampy --port COM3 run ./helpers/motor_setup.py`. You may need to change the serial port ID, depending on the device used.
3. The motor will begin its calibration process. Observe the calibration process to ensure that everything goes smoothly; i.e., motor does not drive force gauge platform past the limits of the testing apparatus.

## Modifying microcontroller code
When code is modified, the code must be transferred to the microcontroller before the next run; e.g., to modify `motor_setup.py`:

```ampy --port COM3 put ./helpers/motor_setup.py ./helpers/motor_setup.py```

# Alternatives
At the time of starting this project, I hadn't seen any ready-built microPython stepper controller code that I liked, but this recent package is an alternate option: https://gist.github.com/nickovs/23928a8591735b00b00654fa628302d5 
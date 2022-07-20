import pygame
from typing import Generator
from enum import IntEnum
import os
from dataclasses import dataclass

os.environ["SDL_VIDEODRIVER"] = "dummy"


class ButtonState(IntEnum):
    Unknown = 0
    Down = 1
    Up = 2


class XboxButton(IntEnum):
    A = 0
    B = 1
    X = 2
    Y = 3
    OPTIONS = 4
    XBOX = 5
    START = 6
    JOY_LEFT = 7
    JOY_RIGHT = 8
    BUMPER_LEFT = 9
    BUMPER_RIGHT = 10
    UP = 11
    DOWN = 12
    LEFT = 13
    RIGHT = 14
    SHARE = 15


class XboxJoystick(IntEnum):
    JOY_LEFT_X = 0
    JOY_LEFT_Y = 1
    JOY_RIGHT_X = 2
    JOY_RIGHT_Y = 3
    TRIGGER_LEFT = 4
    TRIGGER_RIGHT = 5


class LightEventId(IntEnum):
    UnknownEvent = 0x0
    ControllerAdded = 0x1
    ControllerRemoved = 0x2
    Button = 0x10
    ButtonTop = 0x11
    ButtonBottom = 0x12
    ButtonLeft = 0x13
    ButtonRight = 0x14
    ButtonStart = 0x15
    ButtonOptions = 0x16
    ButtonShare = 0x17
    ButtonPower = 0x18
    ButtonStickLeft = 0x19
    ButtonStickRight = 0x1A
    Hat = 0x20
    HatUp = 0x21
    HatDown = 0x22
    HatLeft = 0x23
    HatRight = 0x24
    Bumper = 0x30
    BumperLeft = 0x31
    BumperRight = 0x32
    Trigger = 0x40
    TriggerLeft = 0x41
    TriggerRight = 0x42
    Stick = 0x50
    StickLeft = 0x51
    StickRight = 0x52


@dataclass
class LightEvent:
    controller_instance_id: int
    controller: pygame.joystick.Joystick
    controller_index: int
    event_id: LightEventId

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"controller_index={self.controller_index}"
        )


class LightGame:
    def __init__(self) -> None:
        print("LightGame")
        pygame.init()
        self._controller_instance_dict: dict[int, pygame.joystick.Joystick] = {}
        self._controller_index_dict: dict[int, pygame.joystick.Joystick] = {}
        self._instance_to_index_dict: dict[int, int] = {}

    def get_joysticks(self) -> dict[int, pygame.joystick.Joystick]:
        joystick_count = pygame.joystick.get_count()
        for i in range(joystick_count):
            j = pygame.joystick.Joystick(i)
            if i in self._controller_index_dict:
                self._controller_index_dict[i].quit()
            self._controller_index_dict[i] = j

    def get_events(self) -> Generator[LightEvent, None, None]:
        light_events: list[LightEvent] = []
        left_joysticks: list[LightEvent] = []
        left_joystick_x_count = 0
        left_joystick_y_count = 0
        right_joysticks: list[LightEvent] = []
        right_joystick_x_count = 0
        right_joystick_y_count = 0
        for pygame_event in pygame.event.get():
            if "joy" in pygame_event.dict:
                controller_index = pygame_event.dict["joy"]
                controller_instance_id = pygame_event.dict["instance_id"]
                controller = self._controller_instance_dict[controller_instance_id]
                if "button" in pygame_event.dict:
                    button_id = pygame_event.dict["button"]
                    if button_id == XboxButton.A:
                        light_events.append(
                            ButtonBottom(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.B:
                        light_events.append(
                            ButtonRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.X:
                        light_events.append(
                            ButtonLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.Y:
                        light_events.append(
                            ButtonTop(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.BUMPER_LEFT:
                        light_events.append(
                            ButtonBumperLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.BUMPER_RIGHT:
                        light_events.append(
                            ButtonBumperRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.START:
                        light_events.append(
                            ButtonStart(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.OPTIONS:
                        light_events.append(
                            ButtonOptions(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.XBOX:
                        light_events.append(
                            ButtonPower(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.SHARE:
                        light_events.append(
                            ButtonShare(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.UP:
                        light_events.append(
                            ButtonHatUp(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.DOWN:
                        light_events.append(
                            ButtonHatDown(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.LEFT:
                        light_events.append(
                            ButtonHatLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.RIGHT:
                        light_events.append(
                            ButtonHatRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.JOY_LEFT:
                        light_events.append(
                            ButtonStickLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.JOY_RIGHT:
                        light_events.append(
                            ButtonStickRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    else:
                        print(pygame_event)
                elif "axis" in pygame_event.dict:
                    axis = pygame_event.dict["axis"]
                    if axis == XboxJoystick.JOY_RIGHT_X:
                        if right_joystick_x_count >= len(right_joysticks):
                            light_event = StickRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                            )
                            right_joysticks.append(light_event)
                            light_events.append(light_event)
                        right_joysticks[right_joystick_x_count].x = pygame_event.dict["value"]
                        right_joystick_x_count += 1
                    elif axis == XboxJoystick.JOY_RIGHT_Y:
                        if right_joystick_y_count >= len(right_joysticks):
                            light_event = StickRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                            )
                            right_joysticks.append(light_event)
                            light_events.append(light_event)
                        right_joysticks[right_joystick_y_count].y = pygame_event.dict["value"]
                        right_joystick_y_count += 1
                    elif axis == XboxJoystick.JOY_LEFT_X:
                        if left_joystick_x_count >= len(left_joysticks):
                            light_event = StickLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                            )
                            left_joysticks.append(light_event)
                            light_events.append(light_event)
                        left_joysticks[left_joystick_x_count].x = pygame_event.dict["value"]
                        left_joystick_x_count += 1
                    elif axis == XboxJoystick.JOY_LEFT_Y:
                        if left_joystick_y_count >= len(left_joysticks):
                            light_event = StickLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                            )
                            left_joysticks.append(light_event)
                            light_events.append(light_event)
                        left_joysticks[left_joystick_y_count].y = pygame_event.dict["value"]
                        left_joystick_y_count += 1
                    elif axis == XboxJoystick.TRIGGER_RIGHT:
                        light_events.append(
                            TriggerRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                z=pygame_event.dict["value"],
                            )
                        )
                    elif axis == XboxJoystick.TRIGGER_LEFT:
                        light_events.append(
                            TriggerLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                z=pygame_event.dict["value"],
                            )
                        )
                    else:
                        pass
                        print(pygame_event)
                else:
                    pass
                    print(pygame_event)
            elif pygame_event.type == 1541:
                controller_index = pygame_event.dict["device_index"]
                controller_instance_id = len(self._controller_instance_dict)
                controller = self._controller_index_dict[controller_index]
                self._controller_instance_dict[controller_instance_id] = controller
                self._instance_to_index_dict[controller_instance_id] = controller_index
                light_events.append(
                    ControllerAdded(
                        controller_instance_id=controller_instance_id,
                        controller_index=controller_index,
                        controller=controller,
                    )
                )
            elif pygame_event.type == 1542:
                controller_instance_id = pygame_event.dict["instance_id"]
                controller = self._controller_instance_dict[controller_instance_id]
                controller_index = self._instance_to_index_dict[controller_instance_id]
                light_events.append(
                    ControllerRemoved(
                        controller_instance_id=controller_instance_id,
                        controller_index=controller_index,
                        controller=controller,
                    )
                )
            else:
                print(pygame_event)
        for event in light_events:
            yield event


@dataclass
class ControllerAdded(LightEvent):
    event_id: LightEventId = LightEventId.ControllerAdded


@dataclass
class ControllerRemoved(LightEvent):
    event_id: LightEventId = LightEventId.ControllerRemoved


@dataclass
class ButtonEvent(LightEvent):
    event_id: LightEventId = LightEventId.Button
    state: ButtonState = ButtonState.Unknown

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_index={self.controller_index}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"button_state={self.state.name}"
        )


@dataclass
class ButtonBottom(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonBottom


@dataclass
class ButtonTop(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonTop


@dataclass
class ButtonLeft(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonLeft


@dataclass
class ButtonRight(ButtonEvent):
    event_id = LightEventId.ButtonRight


@dataclass
class ButtonStart(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonStart


@dataclass
class ButtonOptions(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonOptions


@dataclass
class ButtonPower(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonPower


@dataclass
class ButtonShare(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonShare


@dataclass
class ButtonBumper(ButtonEvent):
    event_id: LightEventId = LightEventId.Bumper


@dataclass
class ButtonBumperLeft(ButtonBumper):
    event_id: LightEventId = LightEventId.BumperLeft


@dataclass
class ButtonBumperRight(ButtonBumper):
    event_id: LightEventId = LightEventId.BumperRight


@dataclass
class ButtonHat(ButtonEvent):
    event_id: LightEventId = LightEventId.Hat
    x: float = 0.0
    y: float = 0.0

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_index={self.controller_index}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"(x={self.x:0.2f}, "
            + f"y={self.y:0.2f}), "
            + f"button_state={self.state.name}"
        )


@dataclass
class ButtonHatUp(ButtonHat):
    event_id: LightEventId = LightEventId.HatUp
    y: float = 1.0


@dataclass
class ButtonHatDown(ButtonHat):
    event_id: LightEventId = LightEventId.HatDown
    y: float = -1.0


@dataclass
class ButtonHatLeft(ButtonHat):
    event_id: LightEventId = LightEventId.HatLeft
    x: float = -1.0


@dataclass
class ButtonHatRight(ButtonHat):
    event_id: LightEventId = LightEventId.HatRight
    x: float = 1.0


@dataclass
class ButtonStickLeft(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonStickLeft


@dataclass
class ButtonStickRight(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonStickRight


@dataclass
class Stick(LightEvent):
    event_id: LightEventId = LightEventId.Stick
    x: float = 0.0
    y: float = 0.0

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_index={self.controller_index}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"(x={self.x:0.2f}, "
            + f"y={self.y:0.2f}), "
        )


@dataclass
class StickRight(Stick):
    event_id: LightEventId = LightEventId.StickRight


@dataclass
class StickLeft(Stick):
    event_id: LightEventId = LightEventId.StickLeft


@dataclass
class Trigger(LightEvent):
    event_id: LightEventId = LightEventId.Trigger
    z: float = 0.0

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_index={self.controller_index}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"(z={self.z:0.2f}), "
        )


@dataclass
class TriggerRight(Trigger):
    event_id: LightEventId = LightEventId.TriggerRight


@dataclass
class TriggerLeft(Trigger):
    event_id: LightEventId = LightEventId.TriggerLeft

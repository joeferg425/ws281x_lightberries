#!/usr/bin/python3
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import numpy as np

from lightberries.base.pixel import Pixel, PixelColor
from lightberries.matrix_controller import MatrixController


@dataclass
class rect:
    top: int
    bottom: int
    left: int
    right: int


class SpriteShape(IntEnum):
    CROSS = 0
    CIRCLE = 1
    SQUARE = 2
    RECTANGLE = 3


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


TOP = 1
BOTTOM = 2
LEFT = 4
RIGHT = 8


class CollideEnum(IntEnum):
    NONE = 0  # 0
    TOP = TOP  # 1
    BOTTOM = BOTTOM  # 2
    NOTHING1 = TOP + BOTTOM  # 3
    LEFT = LEFT  # 4
    TOP_LEFT = TOP + LEFT  # 5
    BOTTOM_LEFT = BOTTOM + LEFT  # 6
    MOSTLY_LEFT = TOP + BOTTOM + LEFT  # 7
    RIGHT = RIGHT  # 8
    TOP_RIGHT = TOP + RIGHT  # 9
    BOTTOM_RIGHT = BOTTOM + RIGHT  # 10
    MOSTLY_RIGHT = BOTTOM + TOP + RIGHT  # 11
    NOTHING6 = LEFT + RIGHT  # 12
    MOSTLY_TOP = LEFT + RIGHT + TOP  # 13
    MOSTLY_BOTTOM = LEFT + RIGHT + BOTTOM  # 14
    COLLIDE = LEFT + RIGHT + BOTTOM + TOP  # 15


class GameObject:
    objects: dict[int, GameObject] = {}
    dead_objects: list[GameObject] = []
    frame_size_x: int = 0
    frame_size_y: int = 0
    pause: bool = False
    object_counter: int = 0
    GRAVITY = 0.75
    MAX_GRAVITY = 2.5
    BUTTON_DEBOUNCE = 0.15

    def __init__(
        self,
        x: int,
        y: int,
        size: int,
        name: str,
        shape: SpriteShape = SpriteShape.CROSS,
        color: np.ndarray[(3), np.int32] = PixelColor.WHITE.array,
        has_gravity: bool = True,
        destructible: bool = True,
    ) -> None:
        self._shape = shape
        # self.height = size
        # self.width = size
        self.name = name
        self.owner = None
        self._x = x
        self._y = y
        self.x_last = x
        self.y_last = y
        self._top_last = y
        self._bottom_last = y + size
        self._left_last = x
        self._right_last = x + size
        self._dx = 0.0
        self._dy = 0.0
        self._size = size
        self._color = color
        self.has_gravity = has_gravity
        self.collided: list["GameObject"] = []
        self.destructible = destructible
        self.animate = False
        self.health = 1
        self.max_health = 1
        self.damage = 0
        self.phased = False
        self.timestamp_death: float = time.time()
        self.timestamp_spawn = self.timestamp_death
        self.respawn_delay: float = 1.0
        self.score: int = 0
        self.point_value = 1
        self.id = GameObject.object_counter
        self.children: dict[int, GameObject] = {}
        self.timestamp_ready = self.timestamp_spawn
        self._dead = False
        self.powerup_duration = 1.0
        self.timestamp_powerup = self.timestamp_spawn
        GameObject.objects[GameObject.object_counter] = self
        GameObject.object_counter += 1

    @property
    def x_direction(self):
        if self.dx > 0:
            return 1
        elif self.dx < 0:
            return -1
        else:
            return 0

    @property
    def y_direction(self):
        if self.dy > 0:
            return 1
        elif self.dy < 0:
            return -1
        else:
            return 0

    @property
    def color(self) -> np.ndarray[(3), np.int32]:
        return self._color

    @color.setter
    def color(self, val: np.ndarray[(3), np.int32]) -> None:
        self._color = val

    @property
    def shape(self) -> SpriteShape:
        return self._shape

    @shape.setter
    def shape(self, val: SpriteShape) -> None:
        self._shape = val

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, val: int) -> None:
        self._size = val

    @property
    def height(self) -> int:
        return self._size

    @height.setter
    def height(self, val: int) -> None:
        self._size = val

    @property
    def width(self) -> int:
        return self._size

    @width.setter
    def width(self, val: int) -> None:
        self._size = val

    @property
    def mass2d(self) -> int:
        return self.area2d

    @property
    def area2d(self) -> int:
        if self.shape == SpriteShape.SQUARE:
            return self.width * 2 * self.height * 2
        elif self.shape == SpriteShape.RECTANGLE:
            return self.width * self.height
        elif self.shape == SpriteShape.CROSS:
            return self.width * 2 + self.height * 2
        elif self.shape == SpriteShape.CIRCLE:
            return int(np.pi * self.size * 2)

    def collides_with(self, obj: GameObject) -> CollideEnum:
        o = obj.extended_collision_box
        s = self.extended_collision_box
        c = 0
        c2 = CollideEnum.NONE
        # figure out if we collided at all
        if o.top <= self.bottom:
            c += CollideEnum.BOTTOM
        if o.bottom >= s.top:
            c += CollideEnum.TOP
        if o.right >= s.left:
            c += CollideEnum.LEFT
        if o.left <= s.right:
            c += CollideEnum.RIGHT
        c = CollideEnum(c)
        # figure out where we collided
        if c == CollideEnum.COLLIDE:
            if obj.top <= self.bottom and obj.top >= self.top:
                c2 += CollideEnum.BOTTOM
            if obj.bottom >= self.top and obj.bottom <= self.bottom:
                c2 += CollideEnum.TOP
            if obj.left <= self.right and obj.left >= self.left:
                c2 += CollideEnum.RIGHT
            if obj.right >= self.left and obj.right <= self.right:
                c2 += CollideEnum.LEFT

            # make the return value easier to use
            c2 = CollideEnum(c2)
            if c2 == CollideEnum.MOSTLY_BOTTOM:
                c2 = CollideEnum.BOTTOM
            elif c2 == CollideEnum.MOSTLY_TOP:
                c2 = CollideEnum.TOP
            elif c2 == CollideEnum.MOSTLY_LEFT:
                c2 = CollideEnum.LEFT
            elif c2 == CollideEnum.MOSTLY_RIGHT:
                c2 = CollideEnum.RIGHT
        return c2

    def collide(self, obj: "GameObject", collision: CollideEnum) -> None:
        if not obj.owner == self:
            self.collided.append(obj)
            self.health -= obj.damage
        if self.dead and self.id not in GameObject.dead_objects:
            GameObject.dead_objects.append(self.id)
        if self.animate and not obj.owner == self and not obj.phased:
            if not self.phased:
                if not obj.phased:
                    if self.mass2d < obj.mass2d:
                        if collision & CollideEnum.TOP and self.y_direction > 0:
                            self.bottom = obj.top
                            self.dy = 0
                        elif collision & CollideEnum.BOTTOM and self.y_direction < 0:
                            self.top = obj.bottom + 1
                            self.dy = 0
                        if collision & CollideEnum.LEFT and self.x_direction > 0:
                            self.left = obj.right + 1
                            self.dx = 0
                        elif collision & CollideEnum.RIGHT and self.x_direction < 0:
                            self.right = obj.left
                            self.dx = 0
                    else:
                        pass

    @property
    def collision_box(self) -> rect:
        return rect(
            top=self.top,
            bottom=self.bottom,
            left=self.left,
            right=self.right,
        )

    @property
    def extended_collision_box(self) -> rect:
        return rect(
            top=min(self.top, self.top_last),
            bottom=max(self.bottom, self.bottom_last),
            left=min(self.left, self.left_last),
            right=max(self.right, self.right_last),
        )

    @property
    def dead(self) -> bool:
        return self._dead

    @dead.setter
    def dead(self, value: bool):
        self._dead = value

    @property
    def x(self) -> int:
        return round(self._x)

    @x.setter
    def x(self, value) -> None:
        self.x_last = self._x
        self._left_last = self.left
        self._right_last = self.right
        self._x = value

    @property
    def y(self) -> int:
        return round(self._y)

    @y.setter
    def y(self, value) -> None:
        self.y_last = self._y
        self._top_last = self.top
        self._bottom_last = self.bottom
        self._y = value

    @property
    def top(self) -> int:
        if self.shape == SpriteShape.CROSS or self.shape == SpriteShape.CIRCLE:
            y = self.y - self.height - 1
        else:
            y = self.y - 1
        if y > (GameObject.frame_size_y - 1):
            return GameObject.frame_size_y - 1
        elif y < 0:
            return 0
        else:
            return y

    @top.setter
    def top(self, val: int) -> None:
        if self.shape == SpriteShape.CROSS or self.shape == SpriteShape.CIRCLE:
            self.y = val + self.height + 1
        else:
            self.y = val + 1

    @property
    def top_last(self) -> int:
        return int(self._top_last)

    @property
    def bottom(self) -> int:
        if self.shape == SpriteShape.CROSS or self.shape == SpriteShape.CIRCLE or self.shape == SpriteShape.RECTANGLE:
            y = self.y + self.height - 1
        else:
            y = self.y - 1
        if y > (GameObject.frame_size_y - 1):
            return GameObject.frame_size_y - 1
        elif y < 0:
            return 0
        else:
            return y

    @bottom.setter
    def bottom(self, val: int) -> None:
        if self.shape == SpriteShape.CROSS or self.shape == SpriteShape.CIRCLE or self.shape == SpriteShape.RECTANGLE:
            self.y = val - self.height + 1
        else:
            self.y = val + 1

    @property
    def bottom_last(self) -> int:
        return int(self._bottom_last)

    @property
    def left(self) -> int:
        if self.shape == SpriteShape.CROSS or self.shape == SpriteShape.CIRCLE:
            x = self.x - self.width - 1
        else:
            x = self.x - 1
        if x > (GameObject.frame_size_x - 1):
            return GameObject.frame_size_x - 1
        elif x < 0:
            return 0
        else:
            return x

    @left.setter
    def left(self, val: int) -> None:
        if self.shape == SpriteShape.CROSS or self.shape == SpriteShape.CIRCLE:
            self.x = val + self.width + 1
        else:
            self.x = val + 1

    @property
    def left_last(self) -> int:
        return int(self._left_last)

    @property
    def right(self) -> int:
        if self.shape == SpriteShape.CROSS or self.shape == SpriteShape.CIRCLE or self.shape == SpriteShape.RECTANGLE:
            x = self.x + self.width - 1
        else:
            x = self.x - 1
        if x > (GameObject.frame_size_x - 1):
            return GameObject.frame_size_x - 1
        elif x < 0:
            return 0
        else:
            return x

    @right.setter
    def right(self, val: int) -> None:
        if self.shape == SpriteShape.CROSS or self.shape == SpriteShape.CIRCLE or self.shape == SpriteShape.RECTANGLE:
            self.x = val - self.width + 1
        else:
            self.x = val + 1

    @property
    def right_last(self) -> int:
        return int(self._right_last)

    @property
    def xs(self) -> list[int]:
        if self.shape == SpriteShape.CROSS:
            xs = [round(self._x + i) for i in range(-self.size, self.size + 1)]
            xs.extend([round(self._x) for i in range(-self.size, self.size + 1)])
        elif self.shape == SpriteShape.CIRCLE:
            xs = (
                np.round(np.sin(np.linspace(0, 2 * np.pi, 1 + (4 * self.size))) * (self.size)).astype(dtype=np.int32)
                + self.x
            )
        elif self.shape == SpriteShape.SQUARE:
            xs = []
            _xs = [round(self._x + i) for i in range(-self.size, 0)]
            _xs.extend([round(self._x + i) for i in range(self.size + 1)])
            xs.extend(_xs)
            for _ in range(self.size - 1):
                xs.extend([_xs[0], _xs[-1]])
            xs.extend([_xs[0], _xs[-1]])
            for _ in range(self.size - 1):
                xs.extend([_xs[0], _xs[-1]])
            xs.extend(_xs)
        elif self.shape == SpriteShape.RECTANGLE:
            xs = []
            for _ in range(self.height):
                xs.extend([round(self._x + i) for i in range(self.width + 1)])
        return xs

    @property
    def ys(self) -> list[int]:
        if self.shape == SpriteShape.CROSS:
            ys = [round(self._y) for i in range(-self.size, self.size + 1)]
            ys.extend([round(self._y + i) for i in range(-self.size, self.size + 1)])
        elif self.shape == SpriteShape.CIRCLE:
            ys = (
                np.round(np.cos(np.linspace(0, 2 * np.pi, 1 + (4 * self.size))) * (self.size)).astype(dtype=np.int32)
                + self.y
            )
        elif self.shape == SpriteShape.SQUARE:
            ys = []
            _ys = [round(self._y + i) for i in range(-self.size, 0)]
            _ys.extend([round(self._y + i) for i in range(self.size + 1)])
            counter = 0
            ys.extend([_ys[counter]] * ((self.size * 2) + 1))
            counter += 1
            for _ in range(-self.size + 1, 0):
                ys.extend([_ys[counter], _ys[counter]])
                counter += 1
            ys.extend([_ys[counter], _ys[counter]])
            counter += 1
            for _ in range(self.size - 1):
                ys.extend([_ys[counter], _ys[counter]])
                counter += 1
            ys.extend([_ys[counter]] * ((self.size * 2) + 1))
        elif self.shape == SpriteShape.RECTANGLE:
            ys = []
            for i in range(self.height):
                ys.extend([round(self._y + i) for _ in range(self.width + 1)])
        return ys

    @property
    def xys(self) -> list[tuple[int, int]]:
        return list(zip(self.xs, self.ys))

    @property
    def dx(self) -> int:
        return self._dx

    @dx.setter
    def dx(self, value) -> None:
        self._dx = value

    @property
    def dy(self) -> int:
        return self._dy

    @dy.setter
    def dy(self, value) -> None:
        self._dy = value

    @property
    def x_move(self) -> int:
        return self.x - self.x_last

    @property
    def y_move(self) -> int:
        return self.y - self.y_last

    @property
    def move_max(self) -> int:
        return max(round(self.x_move), round(self.y_move), 1)

    @property
    def move_xs(self) -> list[tuple[int, int]]:
        _dx = float(self.x_move) / self.move_max
        return [round(self.x_last + (_dx * i)) for i in range(self.move_max + 1)]

    @property
    def move_ys(self) -> list[tuple[int, int]]:
        _dy = float(self.y_move) / self.move_max
        return [round(self.y_last + (_dy * i)) for i in range(self.move_max + 1)]

    @property
    def move_xys(self) -> list[tuple[int, int]]:
        return list(zip(self.move_xs, self.move_ys))

    def go(self):
        """Do nothing."""
        pass

    def __str__(self) -> str:
        return (
            f"{self.name}#{self.id} xy:[{self.x},{self.y}], dxdy:[{self.dx:.1f},{self.dy:.1f}],"
            + f"xxyy:[{self.left},{self.right},{self.top},{self.bottom}] ({'dead' if self.dead else 'alive'})"
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}> {self}"

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, (GameObject, tuple)):
            return False
        elif isinstance(obj, tuple):
            return self.x == obj[0] and self.y == obj[1]
        else:
            return self.x == obj.x and self.y == obj.y


class Floor(GameObject):
    def __init__(
        self,
        x: int,
        y: int,
        width: int = 1,
        height: int = 1,
        name: str = "floor",
        color: np.ndarray[(3), np.int32] = PixelColor.ORANGE.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=width,
            shape=SpriteShape.RECTANGLE,
            name=name,
            color=color,
            has_gravity=False,
            destructible=False,
        )
        self._width = width
        self._height = height

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, val: int) -> None:
        self._height = val

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, val: int) -> None:
        self._width = val


class Wall(GameObject):
    def __init__(
        self,
        x: int,
        y: int,
        height: int = 1,
        width: int = 1,
        name: str = "wall",
        color: np.ndarray[(3), np.int32] = PixelColor.WHITE.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            shape=SpriteShape.RECTANGLE,
            size=height,
            name=name,
            color=color,
            has_gravity=False,
            destructible=False,
        )


class Sprite(GameObject):
    def __init__(
        self,
        x: int,
        y: int,
        size: int,
        name: str,
        shape: SpriteShape = SpriteShape.CROSS,
        color: np.ndarray[(3), np.int32] = PixelColor.WHITE.array,
        has_gravity: bool = True,
        destructible: bool = True,
        bounded: bool = True,
        wrap: bool = False,
        dx: float = 0.0,
        dy: float = 0.0,
        health: int = 1,
        max_health: int = 1,
        damage: int = 1,
        phased: bool = False,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
            shape=shape,
            name=name,
            color=color,
            has_gravity=has_gravity,
            destructible=destructible,
        )
        self.animate = True
        self.health = health
        self.max_health = max_health
        self.damage = damage
        self._dead = False
        self.dead_time = 0.0
        self._dx = dx
        self._dy = dy
        self.airborne = False
        self.bounded = bounded
        self.wrap = wrap
        self.phased = phased

    @property
    def xs(self) -> list[int]:
        xs = super().xs
        xs = np.array(xs)
        fix = np.where(xs < 0)
        if fix:
            xs[fix] += GameObject.frame_size_x
        fix = np.where(xs >= GameObject.frame_size_x)
        if fix:
            xs[fix] -= GameObject.frame_size_x
        return [int(x) for x in xs]

    @property
    def ys(self) -> list[int]:
        ys = super().ys
        ys = np.array(ys)
        fix = np.where(ys < 0)
        if fix:
            ys[fix] += GameObject.frame_size_y
        fix = np.where(ys >= GameObject.frame_size_y)
        if fix:
            ys[fix] -= GameObject.frame_size_y
        return [int(y) for y in ys]

    @property
    def move_xs(self) -> list[tuple[int, int]]:
        return self.xs

    @property
    def move_ys(self) -> list[tuple[int, int]]:
        return self.ys

    @property
    def dead(self) -> bool:
        if self._dead:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            if not self._dead:
                self.dead_time = time.time()
                self._dead = True
        elif self.health <= 0:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            if not self._dead:
                self.dead_time = time.time()
                self._dead = True
        elif self.bounded:
            if self.x > (GameObject.frame_size_x - 1) or self.x < 0:
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
                if not self._dead:
                    self.dead_time = time.time()
                    self._dead = True
            elif self.y > (GameObject.frame_size_y - 1) or self.y < 0:
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
                if not self._dead:
                    self.dead_time = time.time()
                    self._dead = True
        if self._dead:
            self.color = PixelColor.YELLOW.array
        return self._dead

    @dead.setter
    def dead(self, value: bool) -> None:
        self._dead = value

    @property
    def move_range(self) -> int:
        return max(self.dx, self.dy)

    @property
    def xy_ray(self) -> tuple[list[int], list[int]]:
        xs = [self.x]
        ys = [self.y]
        rx = self.x
        ry = self.y
        while (
            (GameObject.frame_size_x - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (GameObject.frame_size_y - 1) not in ys
        ):
            rx += self.dx
            ry += self.dy
            if round(rx) not in xs or round(ry) not in ys:
                xs.extend([(round(rx) + i) for i in range(-1, 2)])
                xs.extend([round(rx) for i in range(-1, 2)])
                ys.extend([round(ry) for i in range(-1, 2)])
                ys.extend([(round(ry) + i) for i in range(-1, 2)])
        return xs, ys

    def go(self):
        if not self.dead and not GameObject.pause:
            if self.has_gravity and self.dy < GameObject.MAX_GRAVITY:
                self.dy += GameObject.GRAVITY
            self.x = self._x + self.dx
            self.y = self._y + self.dy
            if self.wrap:
                if self.x >= GameObject.frame_size_x:
                    self.x -= GameObject.frame_size_x
                elif self.x < 0:
                    self.x += GameObject.frame_size_x
                if self.wrap and self.y >= GameObject.frame_size_y:
                    self.y -= GameObject.frame_size_y
                elif self.y < 0:
                    self.y += GameObject.frame_size_y


class Player(Sprite):
    def __init__(
        self,
        x: int,
        y: int,
        size: int = 0,
        name="player",
        color: np.ndarray[(3), np.int32] = PixelColor.GREEN.array,
        has_gravity: bool = True,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
            name=name,
            color=color,
            has_gravity=has_gravity,
            destructible=False,
            bounded=True,
            dx=0.0,
            dy=0.0,
        )
        self.jump_count = 0
        self._x_aim = 0.0
        self._y_aim = 0.0
        self.powerup: Optional[GameObject] = None

    @property
    def x_aim(self) -> float:
        return self._x_aim

    @property
    def x_aim_direction(self) -> float:
        if self._x_aim > 0:
            return 1
        elif self._x_aim < 0:
            return -1
        else:
            return 0

    @x_aim.setter
    def x_aim(self, value: float) -> None:
        self._x_aim = value

    @property
    def y_aim(self) -> float:
        return self._y_aim

    @property
    def y_aim_direction(self) -> float:
        if self._y_aim > 0:
            return 1
        elif self._y_aim < 0:
            return -1
        else:
            return 0

    @y_aim.setter
    def y_aim(self, value: float) -> None:
        self._y_aim = value

    @property
    def xy_ray(self) -> tuple[list[int], list[int]]:
        xs = [self.x]
        ys = [self.y]
        rx = self.x
        ry = self.y
        while (
            (GameObject.frame_size_x - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (GameObject.frame_size_y - 1) not in ys
        ):
            rx += self.dx
            ry += self.dy
            if round(rx) not in xs or round(ry) not in ys:
                xs.extend([(round(rx) + i) for i in range(-1, 2)])
                xs.extend([round(rx) for i in range(-1, 2)])
                ys.extend([round(ry) for i in range(-1, 2)])
                ys.extend([(round(ry) + i) for i in range(-1, 2)])
        return xs, ys

    def go(self):
        if self.collided and self.dy > 0:
            self.jump_count = 0
        if not self.dead and not GameObject.pause:
            self.x = self._x + self.dx
            self.y = self._y + self.dy
            if self.has_gravity and self.dy < GameObject.MAX_GRAVITY:
                self.dy += GameObject.GRAVITY
            if self.wrap:
                if self.x >= GameObject.frame_size_x:
                    self.x -= GameObject.frame_size_x
                elif self.x < 0:
                    self.x += GameObject.frame_size_x
                if self.wrap and self.y >= GameObject.frame_size_y:
                    self.y -= GameObject.frame_size_y
                elif self.y < 0:
                    self.y += GameObject.frame_size_y


class Enemy(Sprite):
    def __init__(
        self,
        x: int,
        y: int,
        size: int = 1,
        name: str = "enemy",
        color: np.ndarray[(3), np.int32] = PixelColor.RED.array,
        destructible: bool = True,
        dx: float = 0.0,
        dy: float = 0.0,
        wrap: bool = False,
        has_gravity: bool = True,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
            name=name,
            color=color,
            has_gravity=has_gravity,
            destructible=destructible,
            bounded=False,
            dx=dx,
            dy=dy,
            wrap=wrap,
        )

    def go(self):
        if not self.dead and not GameObject.pause:
            if self.has_gravity and self.dy < GameObject.MAX_GRAVITY:
                self.dy += GameObject.GRAVITY
            self._x = self._x + self.dx
            self._y = self._y + self.dy
            if self.wrap:
                if self.x >= GameObject.frame_size_x:
                    self.x -= GameObject.frame_size_x
                elif self.x < 0:
                    self.x += GameObject.frame_size_x
                if self.wrap and self.y >= GameObject.frame_size_y:
                    self.y -= GameObject.frame_size_y
                elif self.y < 0:
                    self.y += GameObject.frame_size_y


class Projectile(Sprite):
    def __init__(
        self,
        owner: GameObject,
        x: int,
        y: int,
        size: int = 1,
        name: str = "projectile",
        color: np.ndarray[(3), np.int32] = PixelColor.BLUE.array,
        destructible: bool = True,
        bounded: bool = True,
        dx: float = 0.0,
        dy: float = 0.0,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
            name=name,
            color=color,
            has_gravity=False,
            destructible=destructible,
            bounded=bounded,
            dx=dx,
            dy=dy,
        )
        self.owner = owner
        self.owner.children[self.id] = self
        self.phased = True

    # @property
    # def xs(self) -> list[int]:
    #     x_change = int(self.x_last - self.x)
    #     if x_change != 0:
    #         if x_change > 0:
    #             return [round(self.x_last + i) for i in range(x_change)]
    #         else:
    #             return [round(self.x_last + i) for i in range(0, x_change, -1)]
    #     else:
    #         return [self.x] * (self.move_max)

    # @property
    # def ys(self) -> list[int]:
    #     y_change = int(self.y_last - self.y)
    #     if y_change != 0:
    #         if y_change > 0:
    #             return [round(self.y_last + i) for i in range(y_change)]
    #         else:
    #             return [round(self.y_last + i) for i in range(0, y_change, -1)]
    #     else:
    #         return [self.y] * (self.move_max)

    @property
    def move_xs(self) -> list[tuple[int, int]]:
        x_change = int(self.x_last - self.x)
        if x_change != 0:
            if x_change > 0:
                return [round(self.x_last + i) for i in range(x_change)]
            else:
                return [round(self.x_last + i) for i in range(0, x_change, -1)]
        else:
            return [self.x] * (self.move_max)

    @property
    def move_ys(self) -> list[tuple[int, int]]:
        y_change = int(self.y_last - self.y)
        if y_change != 0:
            if y_change > 0:
                return [round(self.y_last + i) for i in range(y_change)]
            else:
                return [round(self.y_last + i) for i in range(0, y_change, -1)]
        else:
            return [self.y] * (self.move_max)

    @property
    def dead(self) -> bool:
        if self.health <= 0:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            self._dead = True
        elif self.x >= (GameObject.frame_size_x - 1) or self.x <= 0:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            self._dead = True
        elif self.y >= (GameObject.frame_size_y - 1) or self.y <= 0:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            self._dead = True
        return self._dead

    @dead.setter
    def dead(self, value: bool) -> None:
        self._dead = value

    @property
    def xy_ray(self) -> tuple[list[int], list[int]]:
        xs = [self.x]
        ys = [self.y]
        rx = self.x
        ry = self.y
        while (
            (GameObject.frame_size_x - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (GameObject.frame_size_y - 1) not in ys
        ):
            rx += self.dx
            ry += self.dy
            if round(rx) not in xs or round(ry) not in ys:
                xs.extend([(round(rx) + i) for i in range(-1, 2)])
                xs.extend([round(rx) for i in range(-1, 2)])
                ys.extend([round(ry) for i in range(-1, 2)])
                ys.extend([(round(ry) + i) for i in range(-1, 2)])
        return xs, ys

    def go(self):
        if not self.dead and not GameObject.pause:
            self.x = self._x + self.dx
            self.y = self._y + self.dy

    def collide(self, obj: "GameObject", collision: CollideEnum) -> None:
        if obj.id != self.owner.id:
            self.collided.append(obj)
            self.health -= obj.damage
            self.owner.score += obj.point_value
            obj.point_value = 0
            if self.dead and self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)


def check_for_collisions(lights: Optional[MatrixController] = None):
    t = time.time()
    for key in GameObject.dead_objects:
        if key in GameObject.objects:
            o = GameObject.objects[key]
            if o.animate:
                o.timestamp_death = t
            if o.children:
                for child_key in o.children:
                    c = o.children[child_key]
                    if c.animate:
                        c.dead = True
                        GameObject.dead_objects.append(c.id)
                        o.timestamp_death = t
            GameObject.objects.pop(key)
    GameObject.dead_objects.clear()
    if len(GameObject.objects) > 0:
        objs = list(GameObject.objects.values())
        for obj1 in objs:
            obj1.go()
            obj1.collided.clear()
    keys = list(GameObject.objects.keys())
    if len(GameObject.objects) > 1:
        for i, key1 in enumerate(keys[:-1]):
            try:
                obj1 = GameObject.objects[key1]
                for key2 in keys[i + 1 :]:
                    try:
                        obj2 = GameObject.objects[key2]
                        x = CollideEnum.NONE
                        if lights is not None:
                            lights.virtualLEDBuffer[obj1.xs, obj1.ys] = Pixel(obj1.color).array
                            lights.virtualLEDBuffer[obj2.xs, obj2.ys] = Pixel(obj2.color).array
                            lights.copyVirtualLedsToWS281X()
                            lights.refreshLEDs()
                        if obj1.animate or obj2.animate:
                            x = obj1.collides_with(obj2)
                        else:
                            pass
                        if x != CollideEnum.NONE:
                            x2 = obj2.collides_with(obj1)
                            obj1.collide(obj2, x)
                            obj2.collide(obj1, x2)
                    except KeyError:
                        pass
            except KeyError:
                pass
            except KeyError:
                pass
                pass

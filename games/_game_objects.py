#!/usr/bin/python3
from __future__ import annotations
from enum import IntEnum
import numpy as np
from lightberries.pixel import PixelColors
import time

GRAVITY = 0.5
MAX_GRAVITY = 2


class SpriteShape(IntEnum):
    CROSS = 0
    CIRCLE = 1


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


class game_object:
    objects: dict[int, game_object] = {}
    dead_objects: list[game_object] = []
    frame_size_x: int = 0
    frame_size_y: int = 0
    pause: bool = False
    object_counter: int = 0

    def __init__(
        self,
        x: int,
        y: int,
        size: int,
        name: str,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
        has_gravity: bool = True,
        destructible: bool = True,
    ) -> None:
        self.name = name
        self.owner = None
        self.x_last = x
        self.y_last = y
        self._x = x
        self._y = y
        self._dx = 0.0
        self._dy = 0.0
        self.size = size
        self.color = color
        self.has_gravity = has_gravity
        self.collided: list["game_object"] = []
        self.collision_xys: list[tuple[int, int]] = []
        self.destructible = destructible
        self.animate = False
        self.health = 1
        self.max_health = 1
        self.damage = 0
        self.timestamp_death: float = time.time()
        self.timestamp_spawn = self.timestamp_death
        self.respawn_delay: float = 1.0
        self.score: int = 0
        self.point_value = 1
        self.id = game_object.object_counter
        self.children: dict[int, game_object] = {}
        game_object.objects[game_object.object_counter] = self
        game_object.object_counter += 1

    def collide(self, obj: "game_object", xys: list[tuple[int, int]]) -> None:
        if not obj.owner == self:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            if self.dead and self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)

    @property
    def dead(self) -> bool:
        return False

    @property
    def x(self) -> int:
        return round(self._x)

    @x.setter
    def x(self, value) -> None:
        self.x_last = self._x
        self._x = value

    @property
    def y(self) -> int:
        return round(self._y)

    @y.setter
    def y(self, value) -> None:
        self.y_last = self._y
        self._y = value

    @property
    def xs(self) -> list[int]:
        return [self.x]

    @property
    def ys(self) -> list[int]:
        return [self.y]

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
        return f"{self.name}#{self.id} [{self.x},{self.y}]"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}> {self}"

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, (game_object, tuple)):
            return False
        elif isinstance(obj, tuple):
            return self.x == obj[0] and self.y == obj[1]
        else:
            return self.x == obj.x and self.y == obj.y


class floor(game_object):
    def __init__(
        self,
        x: int,
        y: int,
        size: int = 1,
        name: str = "floor",
        color: np.ndarray[(3), np.int32] = PixelColors.ORANGE.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
            name=name,
            color=color,
            has_gravity=False,
            destructible=False,
        )

    @property
    def xs(self) -> list[int]:
        return [round(self.x + i) for i in range(self.x, self.size + 1)]

    @property
    def ys(self) -> list[int]:
        return [round(self.y) for _ in range(self.x, self.size + 1)]


class wall(game_object):
    def __init__(
        self,
        x: int,
        y: int,
        size: int = 1,
        name: str = "wall",
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
            name=name,
            color=color,
            has_gravity=False,
            destructible=False,
        )

    @property
    def xs(self) -> list[tuple[int, int]]:
        return [round(self.x) for i in range(self.x, self.size + 1)]

    @property
    def ys(self) -> list[tuple[int, int]]:
        return [round(self.y - i) for i in range(self.x, self.size + 1)]


class sprite(game_object):
    def __init__(
        self,
        x: int,
        y: int,
        size: int,
        name: str,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
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
        shape: SpriteShape = SpriteShape.CROSS,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
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
        self.shape = shape

    def __str__(self) -> str:
        return f"{self.name}#{self.id} [{self.x},{self.y}] ({'dead' if self.dead else 'alive'})"

    def collide(self, obj: "game_object", xys: list[tuple[int, int]]) -> None:
        super().collide(obj, xys)
        if self.animate and not obj.owner == self:
            if not self.phased:
                self._y = obj.y - self.y_direction

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
    def xs(self) -> list[int]:
        if self.shape == SpriteShape.CROSS:
            xs = [round(self._x + i) for i in range(-self.size, self.size + 1)]
            xs.extend([round(self._x) for i in range(-self.size, self.size + 1)])
        elif self.shape == SpriteShape.CIRCLE:
            xs = (
                np.round(np.sin(np.linspace(0, 2 * np.pi, 1 + (4 * self.size))) * (self.size)).astype(dtype=np.int32)
                + self.x
            )
        xs = np.array(xs)
        fix = np.where(xs < 0)
        if fix:
            xs[fix] += game_object.frame_size_x
        fix = np.where(xs >= game_object.frame_size_x)
        if fix:
            xs[fix] -= game_object.frame_size_x
        return [int(x) for x in xs]

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
        ys = np.array(ys)
        fix = np.where(ys < 0)
        if fix:
            ys[fix] += game_object.frame_size_y
        fix = np.where(ys >= game_object.frame_size_y)
        if fix:
            ys[fix] -= game_object.frame_size_y
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
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            if not self._dead:
                self.dead_time = time.time()
                self._dead = True
        elif self.health <= 0:
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            if not self._dead:
                self.dead_time = time.time()
                self._dead = True
        elif self.bounded:
            if self.x >= (game_object.frame_size_x - 1) or self.x <= 0:
                if self.id not in game_object.dead_objects:
                    game_object.dead_objects.append(self.id)
                if not self._dead:
                    self.dead_time = time.time()
                    self._dead = True
            elif self.y >= (game_object.frame_size_y - 1) or self.y <= 0:
                if self.id not in game_object.dead_objects:
                    game_object.dead_objects.append(self.id)
                if not self._dead:
                    self.dead_time = time.time()
                    self._dead = True
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
            (game_object.frame_size_x - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (game_object.frame_size_y - 1) not in ys
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
        if not self.dead and not game_object.pause:
            if self.has_gravity and self.dy < MAX_GRAVITY:
                self.dy += GRAVITY
            self.x = self._x + self.dx
            self.y = self._y + self.dy
            if self.wrap:
                if self.x >= game_object.frame_size_x:
                    self.x -= game_object.frame_size_x
                elif self.x < 0:
                    self.x += game_object.frame_size_x
                if self.wrap and self.y >= game_object.frame_size_y:
                    self.y -= game_object.frame_size_y
                elif self.y < 0:
                    self.y += game_object.frame_size_y


class player(sprite):
    def __init__(
        self,
        x: int,
        y: int,
        name="player",
        color: np.ndarray[(3), np.int32] = PixelColors.GREEN.array,
        has_gravity: bool = True,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=0,
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
    def xs(self) -> list[int]:
        xs = [round(self._x + i) for i in range(-self.size, self.size + 1)]
        xs.extend([round(self._x) for i in range(-self.size, self.size + 1)])
        return xs

    @property
    def ys(self) -> list[int]:
        ys = [round(self._y) for i in range(-self.size, self.size + 1)]
        ys.extend([round(self._y + i) for i in range(-self.size, self.size + 1)])
        return ys

    @property
    def xy_ray(self) -> tuple[list[int], list[int]]:
        xs = [self.x]
        ys = [self.y]
        rx = self.x
        ry = self.y
        while (
            (game_object.frame_size_x - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (game_object.frame_size_y - 1) not in ys
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
        if not self.dead and not game_object.pause:
            if self.has_gravity and self.dy < MAX_GRAVITY:
                self.dy += GRAVITY
            self.x = self._x + self.dx
            self.y = self._y + self.dy


class enemy(sprite):
    def __init__(
        self,
        x: int,
        y: int,
        size: int = 1,
        name: str = "enemy",
        color: np.ndarray[(3), np.int32] = PixelColors.RED.array,
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
        if not self.dead and not game_object.pause:
            if self.has_gravity and self.dy < MAX_GRAVITY:
                self.dy += GRAVITY
            self._x = self._x + self.dx
            self._y = self._y + self.dy
            if self.wrap:
                if self.x >= game_object.frame_size_x:
                    self.x -= game_object.frame_size_x
                elif self.x < 0:
                    self.x += game_object.frame_size_x
                if self.wrap and self.y >= game_object.frame_size_y:
                    self.y -= game_object.frame_size_y
                elif self.y < 0:
                    self.y += game_object.frame_size_y


class projectile(sprite):
    def __init__(
        self,
        owner: game_object,
        x: int,
        y: int,
        size: int = 1,
        name: str = "projectile",
        color: np.ndarray[(3), np.int32] = PixelColors.BLUE.array,
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

    @property
    def xs(self) -> list[int]:
        x_change = int(self.x_last - self.x)
        if x_change != 0:
            if x_change > 0:
                return [round(self.x_last + i) for i in range(x_change)]
            else:
                return [round(self.x_last + i) for i in range(0, x_change, -1)]
        else:
            return [self.x] * (self.move_max)

    @property
    def ys(self) -> list[int]:
        y_change = int(self.y_last - self.y)
        if y_change != 0:
            if y_change > 0:
                return [round(self.y_last + i) for i in range(y_change)]
            else:
                return [round(self.y_last + i) for i in range(0, y_change, -1)]
        else:
            return [self.y] * (self.move_max)

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
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            self._dead = True
        elif self.x >= (game_object.frame_size_x - 1) or self.x <= 0:
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            self._dead = True
        elif self.y >= (game_object.frame_size_y - 1) or self.y <= 0:
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
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
            (game_object.frame_size_x - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (game_object.frame_size_y - 1) not in ys
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
        if not self.dead and not game_object.pause:
            self.x = self._x + self.dx
            self.y = self._y + self.dy

    def collide(self, obj: "game_object", xys: list[tuple[int, int]]) -> None:
        if obj.id != self.owner.id:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            self.owner.score += obj.point_value
            obj.point_value = 0
            if self.dead and self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)


def check_for_collisions():
    t = time.time()
    for key in game_object.dead_objects:
        if key in game_object.objects:
            o = game_object.objects[key]
            if o.animate:
                o.timestamp_death = t
            if o.children:
                for child_key in o.children:
                    c = o.children[child_key]
                    if c.animate:
                        c.dead = True
                        game_object.dead_objects.append(c.id)
                        o.timestamp_death = t
            game_object.objects.pop(key)
    game_object.dead_objects.clear()
    if len(game_object.objects) > 0:
        for obj1 in game_object.objects.values():
            obj1.go()
            obj1.collided.clear()
        keys = list(game_object.objects.keys())
    if len(game_object.objects) > 1:
        for i, key1 in enumerate(keys[:-1]):
            obj1 = game_object.objects[key1]
            for key2 in keys[i + 1 :]:
                obj2 = game_object.objects[key2]
                x = []
                if obj1.animate and obj2.animate:
                    x = set(obj1.move_xys).intersection(set(obj2.move_xys))
                elif obj1.animate:
                    x = set(obj1.move_xys).intersection(set(obj2.xys))
                elif obj2.animate:
                    x = set(obj1.xys).intersection(set(obj2.move_xys))
                else:
                    pass
                if x:
                    obj1.collide(obj2, x)
                    obj2.collide(obj1, x)

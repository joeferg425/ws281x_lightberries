#!/usr/bin/python3
from __future__ import annotations
import numpy as np
from lightberries.pixel import PixelColors

GRAVITY = 0.5
MAX_GRAVITY = 2


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
        self.destructible = destructible
        self.animate = False
        self.health = 1
        self.max_health = 1
        self.damage = 0
        self.id = game_object.object_counter
        game_object.objects[game_object.object_counter] = self
        game_object.object_counter += 1

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
    floors: dict[int, floor] = {}

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
        floor.floors[game_object.object_counter] = self

    @property
    def xs(self) -> list[int]:
        return [round(self.x + i) for i in range(self.x, self.size + 1)]

    @property
    def ys(self) -> list[int]:
        return [round(self.y) for _ in range(self.x, self.size + 1)]


class wall(game_object):
    walls: dict[int, wall] = {}

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
        wall.walls[game_object.object_counter] = self

    @property
    def xs(self) -> list[tuple[int, int]]:
        return [round(self.x) for i in range(self.x, self.size + 1)]

    @property
    def ys(self) -> list[tuple[int, int]]:
        return [round(self.y - i) for i in range(self.x, self.size + 1)]


class sprite(game_object):
    sprites: dict[int, sprite] = {}

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
        self._dx = dx
        self._dy = dy
        self.airborn = False
        self.bounded = bounded
        self.phased = phased
        sprite.sprites[game_object.object_counter] = self

    def __str__(self) -> str:
        return f"{self.name}#{self.id} [{self.x},{self.y}] ({'dead' if self.dead else 'alive'})"

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
        if self.dy >= 0:
            return 1
        else:
            return -1

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
    def dead(self) -> bool:
        if self._dead:
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            return True
        elif self.health <= 0:
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            return True
        elif not self.bounded:
            return False
        else:
            if self.x >= (game_object.frame_size_x - 1) or self.x <= 0:
                if self.id not in game_object.dead_objects:
                    game_object.dead_objects.append(self.id)
                return True
            elif self.y >= (game_object.frame_size_y - 1):
                if self.id not in game_object.dead_objects:
                    game_object.dead_objects.append(self.id)
                return True
            else:
                return False

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


class player(sprite):
    players: dict[int, player] = {}

    def __init__(
        self,
        x: int,
        y: int,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=0,
            name="player",
            color=PixelColors.GREEN.array,
            has_gravity=True,
            destructible=False,
            bounded=True,
            dx=0.0,
            dy=0.0,
        )
        player.players[game_object.object_counter] = self
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
    enemies: dict[int, enemy] = {}

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
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
            name=name,
            color=color,
            has_gravity=True,
            destructible=destructible,
            bounded=False,
            dx=dx,
            dy=dy,
        )
        enemy.enemies[game_object.object_counter] = self

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
        if not self.dead and not game_object.pause:
            if self.has_gravity and self.dy < MAX_GRAVITY:
                self.dy += GRAVITY
            self._x = self._x + self.dx
            self._y = self._y + self.dy
            # if self._x >= (lightControl.realLEDColumnCount - 1) or self._x <= 0:
            #     if self.bounded:
            #         self.dead = True
            #     elif self.stop:
            #         if self._x >= (lightControl.realLEDColumnCount - 1):
            #             self._x = lightControl.realLEDColumnCount - 1
            #         elif self._x <= 0:
            #             self._x = 0
            # if self._y >= (lightControl.realLEDRowCount - 1) or self._y <= 0:
            #     if self.bounded:
            #         self.dead = True
            #     elif self.stop:
            #         if self._y >= (lightControl.realLEDRowCount - 1):
            #             self._y = lightControl.realLEDRowCount - 1
            #         elif self._y <= 0:
            #             self._y = 0


class projectile(sprite):
    projectiles: dict[int, enemy] = {}

    def __init__(
        self,
        x: int,
        y: int,
        size: int = 1,
        name: str = "projectile",
        color: np.ndarray[(3), np.int32] = PixelColors.BLUE.array,
        destructible: bool = True,
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
            bounded=True,
            dx=dx,
            dy=dy,
        )
        projectile.projectiles[game_object.object_counter] = self

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
    def dead(self) -> bool:
        if self.collided:
            return True
        elif self.x >= (game_object.frame_size_x - 1) or self.x <= 0:
            return True
        elif self.y >= (game_object.frame_size_y - 1) or self.y <= 0:
            return True
        else:
            return False

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
            self._x = self._x + self.dx
            self._y = self._y + self.dy


def check_for_collisions():
    for key in game_object.dead_objects:
        if key in game_object.objects:
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
                    # x = set(obj1.xys).intersection(set(obj2.xys))
                # if not x and not obj1.has_gravity and obj2.has_gravity and obj2.x in obj1.xs:
                #     x = set(range(obj2.y_last, obj2.y, obj2.y_direction)).intersection(obj1.ys)
                # elif not x and not obj2.has_gravity and obj1.has_gravity and obj1.x in obj2.xs:
                #     x = set(range(obj1.y_last, obj1.y, obj1.y_direction)).intersection(obj2.ys)
                if x:
                    obj1.collided.append(obj2)
                    obj1.health -= obj2.damage
                    obj2.collided.append(obj1)
                    obj2.health -= obj1.damage
                    if not obj1.animate and not obj2.animate:
                        pass
                    elif obj2.animate:
                        if not obj2.phased:
                            obj2._y = obj1.y - obj2.y_direction
                    elif obj1.animate:
                        if not obj1.phased:
                            obj1._y = obj2.y - obj1.y_direction
                    else:
                        raise Exception("not handled yet")
                    if obj1.dead and obj1.id not in game_object.dead_objects:
                        game_object.dead_objects.append(obj1.id)
                    if obj2.dead and obj2.id not in game_object.dead_objects:
                        game_object.dead_objects.append(obj2.id)

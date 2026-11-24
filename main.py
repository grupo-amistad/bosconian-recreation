# /// script
# dependencies = [
#   "esper",
# ]
# ///

"""Función Main"""

import asyncio
import sys
from src.engine.game_engine import GameEngine


async def main() -> None:
    engine = GameEngine()
    await engine.run()


if __name__ == "__main__":
    if sys.platform == "emscripten":
        asyncio.create_task(main())
    else:
        asyncio.run(main())
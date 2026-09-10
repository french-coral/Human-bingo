import random
from collections import Counter


class BingoGenerator:
    """Generate Human Bingo grids from a list of proposition strings."""

    def __init__(self, propositions):
        self.propositions = [
            proposition.strip()
            for proposition in propositions
            if isinstance(proposition, str) and proposition.strip()
        ]

    def generateBatch(self, gridSize, batchSize, seed):
        """Generate several grids with a light usage-balancing strategy."""
        if gridSize < 1:
            raise ValueError("Grid size must be at least 1.")

        if batchSize < 1:
            raise ValueError("Number of grids must be at least 1.")

        if not self.propositions:
            raise ValueError("The proposition list is empty.")

        rng = random.Random(seed)
        tileCount = gridSize * gridSize
        usageCounts = Counter()
        generatedGrids = []

        for _ in range(batchSize):
            grid = self._generateOneGrid(
                tileCount,
                usageCounts,
                rng,
            )
            generatedGrids.append(grid)

        return generatedGrids

    def _generateOneGrid(self, tileCount, usageCounts, rng):
        """
        Select propositions for one grid.

        We give less-used propositions a small advantage, but we add
        randomness so that the result still feels random.
        """
        uniqueCount = len(self.propositions)

        if uniqueCount >= tileCount:
            # A small random shuffle gives every proposition a fair chance.
            shuffled = self.propositions[:]
            rng.shuffle(shuffled)

            # Sort by usage only with a little probability. This is deliberately
            # light so that balancing does not turn into a visible pattern.
            if rng.random() < 0.65:
                shuffled.sort(
                    key=lambda proposition: (
                        usageCounts[proposition],
                        rng.random(),
                    )
                )

            selected = shuffled[:tileCount]
        else:
            # Not enough unique propositions: use every proposition at least
            # once, then fill the remaining cells with random propositions.
            selected = self.propositions[:]
            rng.shuffle(selected)

            remainingCount = tileCount - len(selected)

            for _ in range(remainingCount):
                # Prefer propositions with low usage, but only softly.
                weights = self._buildWeights(usageCounts)
                selected.append(rng.choices(self.propositions, weights=weights, k=1)[0])

        rng.shuffle(selected)

        for proposition in selected:
            usageCounts[proposition] += 1

        return selected

    def _buildWeights(self, usageCounts):
        """Create gentle weights: low-use propositions are slightly favored."""
        maximumUsage = max(
            (usageCounts[proposition] for proposition in self.propositions),
            default=0,
        )

        weights = []
        for proposition in self.propositions:
            usage = usageCounts[proposition]
            # The +1 keeps every proposition selectable.
            weight = (maximumUsage - usage) + 1
            weights.append(weight)

        return weights

from gender_bench.probes import (
    BbqProbe,
    DirectProbe,
    DiscriminationTamkinProbe,
    DiversityMedQaProbe,
    DreadditProbe,
    GestCreativeProbe,
    GestProbe,
    HiringAnProbe,
    HiringBloombergProbe,
    InventoriesProbe,
    IsearProbe,
    JobsLumProbe,
)
from gender_bench.probing.harness import Harness


class DefaultHarness(Harness):

    def __init__(self, **kwargs):
        probes = [
            BbqProbe(),
            DirectProbe(),
            DiscriminationTamkinProbe(num_repetitions=3),
            DiversityMedQaProbe(),
            DreadditProbe(num_repetitions=2),
            GestProbe(),
            GestCreativeProbe(
                num_repetitions=4,
            ),
            HiringAnProbe(sample_k=20_000),
            HiringBloombergProbe(),
            InventoriesProbe(
                num_repetitions=5,
            ),
            IsearProbe(),
            JobsLumProbe(num_repetitions=5),
        ]
        super().__init__(probes=probes, **kwargs)

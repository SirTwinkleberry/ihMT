from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from numpy import sqrt, ceil, floor, arange
from pandas import DataFrame, concat
from tqdm import tqdm
from itertools import product


class Model(BaseModel):
    PARENT_KEY: Optional[str] = None

    def __str__(self):
        string = ""
        if self.PARENT_KEY is not None:
            string += str(self.__dict__[self.PARENT_KEY]) + "\n"
        string += f"{f' {self.__class__.__name__.upper()} ':=^40}"
        for key, val in self:
            if key != self.PARENT_KEY and key != "PARENT_KEY":
                string += f"\n - {key:^15} = {val}"
        return string

    def to_dictionary(self) -> dict:
        if self.PARENT_KEY is None:
            return self.model_dump(exclude="PARENT_KEY")
        return self.__dict__[self.PARENT_KEY].to_dictionary() | self.model_dump(
            exclude=[self.PARENT_KEY, "PARENT_KEY"]
        )

    def to_dataframe(self) -> DataFrame:
        if self.PARENT_KEY is None:
            return DataFrame([self.model_dump(exclude="PARENT_KEY")])
        return concat(
            [
                self.__dict__[self.PARENT_KEY].to_dataframe(),
                DataFrame([self.model_dump(exclude=[self.PARENT_KEY, "PARENT_KEY"])]),
            ],
            axis=1,
        )


class Pulse(Model):
    PARENT_KEY: None = None
    r: float = Field(ge=0, le=1)  # Tukey Shape Parameter
    pw: float = Field(ge=0)  # Pulse Width, in ms
    AI: float = Field(ge=0, le=1, hidden=True, default=0)  # Amplitude Integral
    PI: float = Field(ge=0, le=1, hidden=True, default=0)  # Power Integral
    cap_antenna: float = Field(
        ge=0,
        hidden=True,
        default=23,
    )  # Max B1 peak that the antenna can give for a pulse, in µT
    FA: Optional[Annotated[float, Field(ge=0)]] = None  # Flip Angle of pulse, in °
    B1_mean: Optional[Annotated[float, Field(ge=0)]] = (
        None  # Average B1 as if square pulse, in µT
    )
    B1_peak: Optional[Annotated[float, Field(ge=0)]] = (
        None  # Peak B1 within pulse, in µT
    )
    B1_rms_pulse: Optional[Annotated[float, Field(ge=0)]] = (
        None  # Root Mean Squared from B1 Peak and PI, in µT
    )
    is_sine_mod: bool  # Whether to apply a sqrt(2) factor or not on cap_antenna
    round_FA_down: bool = (
        False  # Whether to ensure Flip Angle is an integer and not bigger than cap_antenna
    )

    def model_post_init(self, __context):
        if self.is_sine_mod:
            self.cap_antenna = self.cap_antenna / sqrt(2)

        self.AI = 1 - self.r * 0.5
        self.PI = 1 - self.r * 5 / 8

        if (
            self.FA is None
            and self.B1_mean is None
            and self.B1_peak is None
            and self.B1_rms_pulse is None
        ):
            self.B1_peak = self.cap_antenna

        if (
            self.FA is not None
            and self.B1_mean is None
            and (
                bool(self.B1_mean) == bool(self.B1_peak)
                and bool(self.B1_mean) == bool(self.B1_rms_pulse)
            )
        ):
            self._compute_B1s_from_FA()

        elif self.FA is None and (
            self.B1_mean is not None
            or self.B1_peak is not None
            or self.B1_rms_pulse is not None
        ):
            self._compute_other_B1s_from_a_B1()

            # Compute FA from B1
            self.FA = 180 * 2 * 42.576 * self.pw * 1e-3 * self.B1_mean

        else:
            raise ValueError(
                "Either Flip Angle `FA` or one of the B1 must be provided, but not both."
            )

        if self.round_FA_down:
            self.FA = floor(self.FA)
            self._compute_B1s_from_FA()  # Recompute B1s from new rounded FA

        if self.B1_peak > self.cap_antenna:
            raise ValueError(
                f"{self.B1_peak=} cannot be greater than the threshold power set for the antenna {self.cap_antenna=}."
            )

    def _compute_B1s_from_FA(self):
        self.B1_mean = (
            self.B1_mean
            if self.B1_mean
            else self.FA / (180 * 2 * 42.576 * self.pw * 1e-3)
        )
        self.B1_peak = self.B1_peak if self.B1_peak else self.B1_mean / self.AI
        self.B1_rms_pulse = (
            self.B1_rms_pulse
            if self.B1_rms_pulse
            else sqrt(self.B1_peak * self.B1_peak * self.PI)
        )

    def _compute_other_B1s_from_a_B1(self):
        if self.B1_mean is not None:
            if self.B1_peak is not None or self.B1_rms_pulse is not None:
                raise ValueError("Provide one of the 3 B1, but not all 3.")
            self.B1_peak = self.B1_mean / self.AI
            self.B1_rms_pulse = sqrt(self.B1_peak * self.B1_peak * self.PI)

        elif self.B1_peak is not None:
            if self.B1_rms_pulse is not None:
                raise ValueError("Provide one of the 3 B1, but not all 3.")
            self.B1_mean = self.B1_peak * self.AI
            self.B1_rms_pulse = sqrt(self.B1_peak * self.B1_peak * self.PI)

        else:
            self.B1_peak = self.B1_rms_pulse / (self.PI * self.PI)
            self.B1_mean = self.B1_peak * self.AI


class Burst(Model):
    PARENT_KEY: str = "pulse"
    pulse: Pulse  # Associated pulses
    dt: float = Field(ge=0)  # Delay between pulses, in ms
    NP: int = Field(ge=0)  # Number of pulses
    N_switch: Optional[Annotated[int, Field(ge=0)]] = (
        None  # Number of same offset pulses before switch
    )
    t_burst: Optional[Annotated[float, Field(ge=0)]] = None  # Duration of burst, in ms
    B1_rms_burst: Optional[Annotated[float, Field(ge=0)]] = (
        None  # Root Mean Squared from NP * pw, t burst, and B1 rms pusle, in µT
    )

    def model_post_init(self, __context):
        if round(self.dt, 8) < round(self.pulse.pw, 8):
            raise AssertionError(
                f"Delay between pulses ({self.dt} ms) cannot be shorter than pulse duration ({self.pulse.pw} ms)."
            )

        if not self.pulse.is_sine_mod:
            if (
                (self.N_switch is None)
                or (self.NP == self.N_switch)
                or (self.N_switch == 0)
                or ((self.NP % self.N_switch) != 0)
            ):
                raise AssertionError(
                    f"N switch ({self.N_switch}) must be an integer multiple of the number of pulses ({self.NP})."
                )
        else:
            if (self.N_switch is not None) and (self.N_switch != 0):
                raise ValueError(
                    f"N_switch ({self.N_switch}) cannot be set to a value if using sine modulated pulses."
                )

        self.t_burst = (
            self.t_burst if self.t_burst else (self.NP - 1) * self.dt + self.dt
        )

        if round(self.t_burst, 8) < round((self.NP - 1) * self.dt + self.pulse.pw, 8):
            raise AssertionError(
                f"Burst duration ({self.t_burst} ms) cannot be shorter than the the number of pulses minus 1 ({self.NP - 1}) times the delay between pulses ({self.dt} ms) + a pulse duration ({self.pulse.pw} ms)."
            )

        self.B1_rms_burst = (
            self.B1_rms_burst
            if self.B1_rms_burst
            else self.pulse.B1_rms_pulse * sqrt(self.pulse.pw / self.dt)
        )  # self.NP cancels itself in the ratio


class Boost(Model):
    PARENT_KEY: str = "burst"
    burst: Burst  # Associated Burst
    t_boost: float = Field(ge=0)  # Duration, in ms
    DC_boost: Optional[Annotated[float, Field(ge=0)]] = None  # Duty Cycle, in %
    B1_rms_boost: Optional[Annotated[float, Field(ge=0)]] = (
        None  # Root Mean Squared from Np * pw, t boost, and B1 rms pusle, in µT
    )

    def model_post_init(self, __context):
        if round(self.t_boost, 8) < round(self.burst.t_burst, 8):
            raise AssertionError(
                f"Boost duration ({self.t_boost} ms) cannot be shorter the burst duration ({self.burst.t_burst} ms)."
            )

        self.DC_boost = (
            self.DC_boost
            if self.DC_boost
            else 100 * self.burst.pulse.pw * self.burst.NP / self.t_boost
        )
        self.B1_rms_boost = (
            self.B1_rms_boost
            if self.B1_rms_boost
            else self.burst.B1_rms_burst * sqrt(self.burst.t_burst / self.t_boost)
        )


class Preparation(Model):
    PARENT_KEY: str = "boost"
    boost: Boost  # Associated Boost
    NB: int = Field(ge=0)  # Number of Boosted Bursts
    t_last_boost: Optional[Annotated[float, Field(ge=0)]] = (
        None  # Last boost duration before readout, in ms
    )
    t_prep: Optional[Annotated[float, Field(ge=0)]] = None  # Duration, in ms
    B1_rms_prep: Optional[Annotated[float, Field(ge=0)]] = (
        None  # Root Mean Squared from Np * pw * Nb, t preparation, and B1 rms pulse, in µT
    )

    def model_post_init(self, __context):
        if (
            bool(self.t_last_boost) == bool(self.t_prep)
        ) and self.t_last_boost is not None:
            raise ValueError(
                "Either of `t_last_boost` or `t_prep` must be provided, but not both."
            )

        t_min_burst = (
            self.boost.burst.NP - 1
        ) * self.boost.burst.dt + self.boost.burst.pulse.pw

        if self.t_last_boost is not None:
            if round(self.t_last_boost, 8) < round(t_min_burst, 8):
                raise AssertionError(
                    f"Last boost duration ({self.t_last_boost} ms) cannot be shorter than the shortest burst duration ({t_min_burst} ms)."
                )

            self.t_prep = self.boost.t_boost * (self.NB - 1) + self.t_last_boost

        else:
            self.t_prep = self.boost.t_boost * (self.NB - 1) + t_min_burst

        if round(self.t_prep, 8) < round(
            self.boost.t_boost * (self.NB - 1) + t_min_burst, 8
        ):
            raise AssertionError(
                f"Preparation duration ({self.t_prep=} ms) cannot be shorter than the burst duration ({self.boost.t_boost} ms) times the number of bursts minus 1 ({self.NB - 1}) plus the shortest burst duration ({t_min_burst} ms)."
            )

        self.B1_rms_prep = (
            self.B1_rms_prep
            if self.B1_rms_prep
            else self.boost.B1_rms_boost
            * sqrt(self.NB * self.boost.t_boost / self.t_prep)
        )


class Sequence(Model):
    PARENT_KEY: str = "prep"
    prep: Preparation  # Associated saturation preparation
    PF_sat: float = Field(ge=0, le=1)  # Partial Fourier
    recovery: float = Field(ge=0, default=0)  # Recovery Delay, in ms
    turbo: Optional[Annotated[int, Field(ge=0)]] = None  # Number of readout segments
    es: Optional[Annotated[float, Field(ge=0)]] = None  # Echo Spacing, in ms
    FA_readout: Optional[Annotated[float, Field(ge=0)]] = (
        None  # Flip Angle of the readout pulses, in °
    )
    TR: Optional[Annotated[float, Field(ge=0)]] = None  # Repeat Duration, in ms
    B1_rms_10s: Optional[Annotated[float, Field(ge=0)]] = (
        None  # B1 rms over 10 seconds, in µT
    )
    B1_rms_6m: Optional[Annotated[float, Field(ge=0)]] = (
        None  # B1 rms over 6 minutes, in µT
    )
    lim_10s: Optional[float] = (
        1.595130854  # B1 rms proxy to SAR limits over 10 seconds, in µT
    )
    round_to_upper_left_3_digits: bool = (
        False  # Whether to ensure that TR is exactly what can be put in the Siemens VE UI and never lower than min TR to be under SAR threshold
    )
    TR_checking: bool = False

    def model_post_init(self, __context):
        # Raise an error if only turbo or echo spacing were provided but not both because you assume a user input error
        if bool(self.turbo) != bool(self.es):
            raise ValueError(
                "Both number of readout segments `turbo` and echo spacing `es` must be provided when `TR` or a B1 rms is not provided."
            )

        # If at least one B1 RMS is provided, compute the other B1 RMS and TR
        if bool(self.B1_rms_6m) != bool(self.B1_rms_10s) or self.B1_rms_10s is not None:
            # Raise an error if both B1 RMSs were provided because you don't know which is the one to use as basis for computation
            if self.B1_rms_6m is not None and self.B1_rms_10s is not None:
                raise ValueError(
                    "Either of `B1_rms_10s` or `B1_rms_6m` must be provided, but not both."
                )

            # Compute the other B1 RMS using the one provided
            self.B1_rms_10s = (
                self.B1_rms_10s
                if self.B1_rms_10s
                else self.B1_rms_6m / sqrt(self.PF_sat)
            )
            self.B1_rms_6m = (
                self.B1_rms_6m
                if self.B1_rms_6m
                else self.B1_rms_10s * sqrt(self.PF_sat)
            )

            # Raise an error if both a B1 RMS and a TR were provided because you don't know which is the one to use as basis for computation
            if self.TR is not None:
                raise ValueError(
                    "Either of `TR` or (`B1_rms_10s` or `B1_rms_6m`) can be provided, but not both."
                )

            # If ==> user has provided a readout scheme, then ==> use it and B1 RMS to constrain TR, else ==> use only B1 RMS to constrain TR
            if self.turbo is not None:
                self.TR = max(
                    self.prep.t_prep + self.es * self.turbo,
                    self.prep.t_prep
                    * (self.prep.B1_rms_prep * self.prep.B1_rms_prep)
                    / (self.B1_rms_10s * self.B1_rms_10s),
                )
            else:
                self.TR = (
                    self.prep.t_prep
                    * (self.prep.B1_rms_prep * self.prep.B1_rms_prep)
                    / (self.B1_rms_10s * self.B1_rms_10s)
                )

        # If ==> neither TR nor B1 RMs were provided, then ==> compute min TR
        if self.TR is None:
            # Raise an error if neither a readout scheme nor a B1 RMS was provided because you don't have enough information to constrain TR
            if self.turbo is None and self.es is None:
                raise ValueError(
                    "Either of `TR` or (`turbo` and `es`) or a B1 rms must be provided."
                )

            self.TR = self.prep.t_prep + self.turbo * self.es + self.recovery

        # String shenanigans to ensure only the 3 left-most digits will count (and be rounded up) for TR
        if self.round_to_upper_left_3_digits:
            self.TR = int(
                float(
                    str(ceil(float(f"{self.TR:.4e}"[:6]) * 100) * 0.01)
                    + f"{self.TR:.4e}"[-4:]
                )
            )

        es = self.es if self.es is not None else 0
        turbo = self.turbo if self.turbo is not None else 0

        if round(self.TR, 8) < round(self.prep.t_prep + es * turbo + self.recovery, 8):
            raise AssertionError(
                f"TR ({self.TR=} ms) cannot be shorter than the preparation time ({self.prep.t_prep} ms) + number of readouts ({turbo}) times the echo spacing ({es} ms) + the recovery delay ({self.recovery} ms)."
            )

        # if ==> TR was provided <-- or --> if ==> TR and B1 RMSs were not provided, then ==> compute the B1 RMSs from TR, else ==> keep their initial value
        self.B1_rms_10s = self.prep.B1_rms_prep * sqrt(self.prep.t_prep / self.TR)
        self.B1_rms_6m = self.B1_rms_10s * sqrt(self.PF_sat)

        # SAR constraints errors
        if round(self.lim_10s, 8) < round(self.B1_rms_10s, 8):
            raise AssertionError(
                f"B1 RMS over 10 seconds ({self.B1_rms_10s} µT) cannot exceed the 10 seconds limit set ({self.lim_10s} µT)."
            )


class ShortTukey(Pulse):
    r: float = 0.3
    pw: float = 1


class LongTukey(Pulse):
    r: float = 0.2
    pw: float = 5.0


if __name__ == "__main__":

    def do_stuff(
        SINE, PWS_DTS, NPS, N_SWITCHES, BTRS, NBS, ES, TURBOS, FA_READOUTS, CAP_ANTENNAS
    ):
        for cap in CAP_ANTENNAS:
            for pw, dt in PWS_DTS:
                pulse = Pulse(
                    r=0.2,
                    pw=pw,
                    is_sine_mod=SINE,
                    round_FA_down=True,
                    cap_antenna=cap,
                )

                for np in NPS:
                    for N_switch in N_SWITCHES:
                        if (not sine) and ((np == N_switch) or (np % N_switch != 0)):
                            continue

                        burst = Burst(pulse=pulse, dt=dt, NP=np, N_switch=N_switch)

                        for btr in tqdm(BTRS):
                            boost = Boost(burst=burst, t_boost=btr)

                            for nb in NBS:
                                # Adding 1ms to prep using t_last_boost as a proxy, as per what we do manually on the 7T console
                                prep = Preparation(
                                    boost=boost, NB=nb, t_last_boost=np * dt + 1
                                )

                                for es, turbo in product(ES, TURBOS):
                                    FA_readout = FA_READOUTS[0]
                                    seq = Sequence(
                                        prep=prep,
                                        PF_sat=1.0,
                                        turbo=turbo,
                                        es=es,
                                        FA_readout=FA_readout,
                                        B1_rms_10s=1.595130854,
                                        round_to_upper_left_3_digits=True,
                                        TR_checking=False,
                                    )

                                    for FA_readout in FA_READOUTS:
                                        seq.FA_readout = FA_readout

                                        yield seq.to_dictionary()

    try:
        BASEPATH = "./"

        COLS = [
            "is_sine_mod",
            "cap_antenna",
            "r",
            "B1_rms_pulse",
            "FA",
            "pw",
            "dt",
            "NP",
            "N_switch",
            "t_burst",
            "t_boost",
            "DC_boost",
            "B1_rms_prep",
            "B1_rms_burst",
            "B1_rms_boost",
            "NB",
            "t_last_boost",
            "PF_sat",
            "recovery",
            "turbo",
            "es",
            "FA_readout",
            "TR",
            "B1_rms_10s",
            "B1_rms_6m",
        ]

        CAP_ANTENNA = [23, 24, 25, 26]
        SINES = [True]
        BTRS = arange(50, 205, 5)
        NBS = [2, 3, 4, 5, 6, 7]
        N_SWITCHES = [0]
        NPS = [1, 2, 3]
        PWS_DTS = [(3.0, 4.08), (3.5, 4.58), (4.0, 5.08), (4.5, 5.58), (5.0, 6.08)]
        TURBOS = [147]
        FA_READOUTS = [5]
        ES = [5.9]

        dict_list = list()

        for sine in SINES:
            n_switch = [0] if sine else N_SWITCHES
            for tmp in do_stuff(
                sine,
                PWS_DTS,
                NPS,
                n_switch,
                BTRS,
                NBS,
                ES,
                TURBOS,
                FA_READOUTS,
                CAP_ANTENNA,
            ):
                dict_list.append(tmp)

        df = DataFrame.from_dict(dict_list)[COLS]

        df.insert(0, "ID", df.index)

        print(df)

        df.to_pickle(BASEPATH + "df_entries_to_ihMTfit.pkl")

    except Exception as e:
        print(e)

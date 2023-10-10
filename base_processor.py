import awkward as ak
from coffea.analysis_tools import PackedSelection
from pocket_coffea.workflows.base import BaseProcessorABC
from pocket_coffea.utils.configurator import Configurator

class OpendataBaseProcessor(BaseProcessorABC):
    '''This is the base processor for the CMS opendata 2012 dataset.
    In order for the processor to work, the following functions need to be implemented:
    - load_metadata_extra: set the MC weights to 1 for each event
    - skim_events: given that the HLT branch is not available in data, the function is modified to skip the HLT skim
    - get_shape_variations: since there is no jet collection, we don't need to loop over shape variations'''

    def __init__(self, cfg: Configurator):
        super().__init__(cfg)

    # Since the CMS opendata NanoAOD file does not have the 'genWeight' branch, we set it to 1 for each event in this demo
    def load_metadata_extra(self):
        if self._isMC:
            self.events["genWeight"] = ak.ones_like(self.events.event, dtype=float)

    # Here we customize the skim_events function to make it compatible with the 2012 Opendata dataset
    def skim_events(self):
        self._skim_masks = PackedSelection()

        if self._isMC:
            for skim_func in self._skim:
                # Apply the skim function and add it to the mask
                mask = skim_func.get_mask(
                    self.events,
                    processor_params=self.params,
                    year=self._year,
                    sample=self._sample,
                    isMC=self._isMC,
                )
                self._skim_masks.add(skim_func.id, mask)
        else:
            for skim_func in self._skim:
                # Apply the skim function and add it to the mask
                try:
                    mask = skim_func.get_mask(
                        self.events,
                        processor_params=self.params,
                        year=self._year,
                        sample=self._sample,
                        isMC=self._isMC,
                    )
                    self._skim_masks.add(skim_func.id, mask)
                except:
                    print(f"The skim function {skim_func.name} is not applied to the sample {self._sample}")
                    continue

        self.events = self.events[self._skim_masks.all(*self._skim_masks.names)]
        self.nEvents_after_skim = self.nevents
        self.output['cutflow']['skim'][self._dataset] = self.nEvents_after_skim
        self.has_events = self.nEvents_after_skim > 0

    # Since there is no jet collection, we don't need to loop over shape variations
    def get_shape_variations(self):
        '''
        Dummy generator for shape variations.
        '''
        yield "nominal"
        return

class ZmumuBaseProcessor(OpendataBaseProcessor):

    def apply_object_preselection(self, variation):
        '''
        The object preselection cleans the following collections:
          - Muons
        In addition, a dilepton object is built.
        '''
        # Build masks for selection of muons
        cuts = self.params.object_preselection["Muon"]

        # Requirements on pT and eta
        passes_eta = abs(self.events.Muon.eta) < cuts["eta"]
        passes_pt = self.events.Muon.pt > cuts["pt"]
    
        # Requirements on isolation
        passes_iso = self.events.Muon.pfRelIso04_all < cuts["iso"]

        good_muons = passes_eta & passes_pt & passes_iso #& passes_id

        self.events["MuonGood"] = self.events.Muon[good_muons]

    def define_common_variables_after_presel(self, variation):
        self.events["ll"] = self.events.MuonGood[:,0] + self.events.MuonGood[:,1]
        fields = {
            "pt": self.events.ll.pt,
            "eta": self.events.ll.eta,
            "phi": self.events.ll.phi,
            "mass": self.events.ll.mass,
            "charge": self.events.ll.charge,
        }
        self.events["ll"] = ak.zip(fields, with_name="PtEtaPhiMCandidate")

    def count_objects(self, variation):
        self.events["nMuonGood"] = ak.num(self.events.MuonGood)

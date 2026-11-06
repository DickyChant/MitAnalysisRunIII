// TMVA XML inference for RDataFrame, one reader per slot (TMVA::Reader is not thread safe).
// Wraps the public TMVA::Experimental::RReader instead of TMVA internals: the internal XMLConfig renamed
// "expressions" to "variable_expressions" and added spectators in ROOT 6.36, which broke the previous
// version; RReader handles both and keeps the same API across ROOT releases.
#include "TMVA/RReader.hxx"

class tmva_xml {

    public:
        tmva_xml(const std::string &filename) : fReader(std::make_unique<TMVA::Experimental::RReader>(filename)) {
            fNumVars = fReader->GetVariableNames().size();
        }

        std::vector<float> Compute(const Vec_f &x) {
            if (x.size() != fNumVars)
                throw std::runtime_error("Size of input vector is not equal to number of variables.");
            return fReader->Compute(std::vector<float>(x.begin(), x.end()));
        }

    private:
        std::unique_ptr<TMVA::Experimental::RReader> fReader;
        std::size_t fNumVars;
};

class tmva_helper_xml {
    public:
        tmva_helper_xml(const std::string &filename, const unsigned int nslots = 1) {
            const unsigned int nslots_actual = std::max(nslots, 1U);
            for (unsigned int islot = 0; islot < nslots_actual; ++islot) {
                interpreters_.emplace_back(std::make_shared<tmva_xml>(filename));
            }
        }

        std::vector<float> operator()(unsigned int slot, const Vec_f vars) {
            return interpreters_[slot]->Compute(vars);
        }

    private:
        std::vector<std::shared_ptr<tmva_xml>> interpreters_;   // shared: RDataFrame copies the callable
};

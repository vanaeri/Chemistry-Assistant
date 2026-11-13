from bakery import assert_equal
from dataclasses import dataclass
from drafter import *
from chempy import Reaction 
from chempy import Substance

set_website_title("Chemistry Assistant")
set_site_information(
    author="Vansh Aeri",
    description="Calculates limiting reactants, theoretical yield, percent yield, and heat flow from given info.",
    sources="",
    planning=["CS1 Final Project 0_ Pick a Problem.pdf", "CS1 Final Project 1_ Design.pdf"],
    links=["https://github.com/vanaeri/Chemistry-Assistant"]
)
hide_debug_information()
set_website_framed(False)

@dataclass
class Chemical:
    formula: str
    starting_mass: float
    ending_mass: float
    moles: float
    molar_mass: float
    coefficient: int
    chosen_product: bool
    role: str


@dataclass
class State:
    reaction: str
    chemicals: list[Chemical]
    reactant_masses: str
    harvested_product_mass: float
    limiting_reactant: str
    theoretical_yield: float
    percent_yield: float
    heat_of_reaction: float
    enthalpies_of_formation: str


@route
def index(state: State) -> Page:
    """Display the homepage and collect a balanced chemical equation."""
    return Page(
        state,
        [
            Header("Chemistry Assistant"),
            "This program calculates limiting reactants, theoretical yield, percent yield, and heat flow.",
            TextBox("reaction", state.reaction),
            Button("Continue", "parse_reaction")
        ]
    )


@route
def parse_reaction(state: State, reaction: str) -> Page:
    """Parse the reaction and create Chemical objects."""
    if reaction == "":
        return Page(
            state,
            [
                Header("Error"),
                "Please enter a reaction.",
                Button("Back", "index")
            ]
        )

    if "->" not in reaction:
        return Page(
            state,
            [
                Header("Error"),
                "Reaction must contain ->",
                Button("Back", "index")
            ]
        )

    state.reaction = reaction
    state.chemicals = []

    # ChemPy parses the chemical equation into reactants and products,
    # including their stoichiometric coefficients.
    reaction_data = Reaction.from_string(reaction)

    for formula, coefficient in reaction_data.reac.items():
        chemical = Chemical(
            formula=formula,
            starting_mass=0.0,
            ending_mass=0.0,
            moles=0.0,
            # ChemPy calculates the molar mass from the chemical formula.
            molar_mass=Substance.from_formula(formula).mass,
            coefficient=coefficient,
            chosen_product=False,
            role="reactant"
        )
        state.chemicals.append(chemical)

    first_product = True

    for formula, coefficient in reaction_data.prod.items():
        chemical = Chemical(
            formula=formula,
            starting_mass=0.0,
            ending_mass=0.0,
            moles=0.0,
            molar_mass=Substance.from_formula(formula).mass,
            coefficient=coefficient,
            chosen_product=first_product,
            role="product"
        )
        state.chemicals.append(chemical)
        first_product = False

    return reactant_masses(state)


@route
def reactant_masses(state: State) -> Page:
    """Display all reactants and collect mass information."""
    reactant_list = ""

    for chemical in state.chemicals:
        if chemical.role == "reactant":
            reactant_list += chemical.formula + "\n"

    return Page(
        state,
        [
            Header("Reactant Masses"),
            "Enter the masses of the reactants in grams, separated by commas.",
            reactant_list,
            TextBox("reactant_masses", state.reactant_masses),
            Button("Continue", "product_selection")
        ]
    )


@route
def product_selection(state: State, reactant_masses: str) -> Page:
    """Display product selection information."""
    state.reactant_masses = reactant_masses

    selected_product = ""

    for chemical in state.chemicals:
        if chemical.chosen_product:
            selected_product = chemical.formula

    if selected_product == "":
        message = "No products selected."
    else:
        message = "Selected Product: " + selected_product

    return Page(
        state,
        [
            Header("Product Selection"),
            message,
            Button("Continue", "actual_yield")
        ]
    )


@route
def actual_yield(state: State) -> Page:
    """Collect the harvested mass of the desired product."""
    return Page(
        state,
        [
            Header("Actual Yield"),
            "Enter the harvested product mass in grams.",
            TextBox(
                "harvested_product_mass",
                str(state.harvested_product_mass)
            ),
            Button("Calculate", "stoichiometry_analysis")
        ]
    )


@route
def stoichiometry_analysis(
    state: State,
    harvested_product_mass: float
) -> Page:
    """Determine the limiting reactant and reaction yields."""

    state.harvested_product_mass = harvested_product_mass

    masses = state.reactant_masses.split(",")

    reactants = []

    for chemical in state.chemicals:
        if chemical.role == "reactant":
            reactants.append(chemical)

    if len(masses) != len(reactants):
        return Page(
            state,
            [
                Header("Error"),
                "Please enter exactly one mass for each reactant.",
                Button("Back", "reactant_masses")
            ]
        )

    limiting_ratio = float("inf")

    for i, chemical in enumerate(reactants):
        chemical.starting_mass = float(masses[i].strip())

        chemical.moles = calculate_moles(
            chemical.starting_mass,
            chemical.molar_mass
        )

        if chemical.coefficient > 0:
            ratio = chemical.moles / chemical.coefficient

            if ratio < limiting_ratio:
                limiting_ratio = ratio
                state.limiting_reactant = chemical.formula

    # Calculate theoretical yield using the limiting reactant.
    state.theoretical_yield = 0.0

    for chemical in state.chemicals:
        if chemical.chosen_product:
            state.theoretical_yield = (
                limiting_ratio
                * chemical.coefficient
                * chemical.molar_mass
            )

    if state.theoretical_yield > 0:
        state.percent_yield = (
            state.harvested_product_mass
            / state.theoretical_yield
        ) * 100

    return Page(
        state,
        [
            Header("Stoichiometry Analysis"),
            "Limiting Reactant: " + state.limiting_reactant,
            "Theoretical Yield: " + str(round(state.theoretical_yield, 2)) + " g",
            "Percent Yield: " + format(state.percent_yield, ".2f") + "%",
            Button("Heat Analysis", "thermochemistry_input")
        ]
    )


def calculate_moles(mass: float, molar_mass: float) -> float:
    """Calculate the number of moles in a sample."""
    if molar_mass == 0:
        return 0

    return mass / molar_mass


def determine_reaction_type(heat: float) -> str:
    """Determine whether a reaction is exothermic or endothermic."""
    if heat < 0:
        return "Exothermic"

    if heat > 0:
        return "Endothermic"

    return "Neither exothermic nor endothermic"


@route
def thermochemistry_input(state: State) -> Page:
    """Collect standard enthalpies of formation."""

    chemical_list = ""

    for chemical in state.chemicals:
        chemical_list += (
            chemical.formula
            + " ("
            + chemical.role
            + ")\n"
        )

    return Page(
        state,
        [
            Header("Thermochemistry"),
            "Enter the standard enthalpies of formation (ΔHf°) in kJ/mol.",
            "Enter one value for every chemical listed below, separated by commas.",
            "Use the same order as the list.",
            chemical_list,
            TextBox(
                "enthalpies_of_formation",
                state.enthalpies_of_formation
            ),
            Button("Calculate Heat", "thermochemistry_results")
        ]
    )


@route
def thermochemistry_results(
    state: State,
    enthalpies_of_formation: str
) -> Page:
    """Calculate reaction enthalpy using formation enthalpies."""

    state.enthalpies_of_formation = enthalpies_of_formation

    values = enthalpies_of_formation.split(",")

    if len(values) != len(state.chemicals):
        return Page(
            state,
            [
                Header("Error"),
                "Please enter exactly one enthalpy value for each chemical.",
                Button("Back", "thermochemistry_input")
            ]
        )

    try:
        enthalpies = []

        for value in values:
            enthalpies.append(float(value.strip()))

    except ValueError:
        return Page(
            state,
            [
                Header("Error"),
                "Please enter valid numerical enthalpy values.",
                Button("Back", "thermochemistry_input")
            ]
        )

    # Calculate the total enthalpy of reactants and products.
    reactant_heat = 0.0
    product_heat = 0.0

    for i, chemical in enumerate(state.chemicals):
        heat = chemical.coefficient * enthalpies[i]

        if chemical.role == "reactant":
            reactant_heat += heat
        else:
            product_heat += heat

    # ΔH reaction = Products - Reactants
    state.heat_of_reaction = product_heat - reactant_heat

    reaction_type = determine_reaction_type(
        state.heat_of_reaction
    )

    return Page(
        state,
        [
            Header("Thermochemistry Results"),
            "Reaction Type: " + reaction_type,
            "Heat of Reaction: " + format(state.heat_of_reaction, ".2f") + " kJ",
            "Limiting Reactant: " + state.limiting_reactant,
            "Theoretical Yield: " + str(round(state.theoretical_yield, 2)) + " g",
            "Percent Yield: " + format(state.percent_yield, ".2f") + "%",
            Button("Start Over", "index")
        ]
    )


# Tests

assert_equal(
    calculate_moles(20, 10),
    2
)

assert_equal(
    determine_reaction_type(-100),
    "Exothermic"
)

assert_equal(
    determine_reaction_type(100),
    "Endothermic"
)

assert_equal(
    determine_reaction_type(0),
    "Neither exothermic nor endothermic"
)

assert_equal(calculate_moles(0, 10), 0)
assert_equal(calculate_moles(50, 10), 5)
assert_equal(calculate_moles(20, 0), 0)

initial_state = State(
    reaction="",
    chemicals=[],
    reactant_masses="",
    harvested_product_mass=0.0,
    limiting_reactant="",
    theoretical_yield=0.0,
    percent_yield=0.0,
    heat_of_reaction=0.0,
    enthalpies_of_formation=""
)

start_server(initial_state)


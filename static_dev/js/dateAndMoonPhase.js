function calculateMoonPhase() {
    const now = new Date(); // Months are 0-indexed in JavaScript
    const newMoonDate = new Date(Date.UTC(2023, 10, 13, 9, 27)); // Known new moon
    const lunarCycle = 29.53058867; // Length of a lunar month
    const daysSinceNewMoon = (now - newMoonDate) / 1000 / 60 / 60 / 24;
    const currentPhase = (daysSinceNewMoon % lunarCycle) / lunarCycle * 8;

    const moonPhases = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'];


    let moonPhaseIndex = Math.floor(currentPhase);
    let nextMoonPhaseIndex = (moonPhaseIndex + 1) % 8;

    // Define a tighter threshold for the main moon phases
    const mainPhaseThreshold = 0.25;


    console.log(moonPhaseIndex);
    console.log(nextMoonPhaseIndex);
    console.log(moonPhases[moonPhaseIndex]);
    console.log(moonPhases[nextMoonPhaseIndex]);
    console.log(currentPhase);

    // Check if the current phase is one of the main phases, assign on threshold basis
    if (moonPhaseIndex % 2 === 0) {
        if (currentPhase - moonPhaseIndex < mainPhaseThreshold) {
            return moonPhases[moonPhaseIndex];
        } else
        return moonPhases[nextMoonPhaseIndex];
    } else {
        if (nextMoonPhaseIndex === 0) {
            nextMoonPhaseIndex = 8;
        }
        if (nextMoonPhaseIndex - currentPhase < mainPhaseThreshold) {
            nextMoonPhaseIndex = nextMoonPhaseIndex % 8;
            return moonPhases[nextMoonPhaseIndex];
        } else
        return moonPhases[moonPhaseIndex];
    }


}

function updateLabel() {
    const today = new Date();
    const dateString = today.toLocaleDateString();
    const moonPhaseEmoji = calculateMoonPhase();

    document.getElementById("dateAndMoonPhase").innerText = `${dateString} | ${moonPhaseEmoji}`;
}

document.addEventListener('DOMContentLoaded', updateLabel);

if (!(navigator.deviceMemory == 2)) {
	new BugController({
		imageSprite: "/i/fireflies.webp",
		canDie: false,
		minBugs: 10,
		maxBugs: 30,
		mouseOver: "multiply"
	});
}

# Future Combat Mechanics - Design Notes

## Step-Forward Mechanic (Future Consideration)

**Concept:** Quick aggressive movement TOWARD enemy (opposite of dodge)

**Design Intent:**

- Offensive positioning option
- Complements defensive dodge (away) and parry (stillness)
- Generates momentum for damage bonus
- Risk/reward: close gap but commit to aggression

**Potential Implementation:**

- Input: Double-tap forward or dedicated key
- Effect: Quick dash toward locked target/camera direction
- Distance: ~2-3 units (shorter than dodge)
- I-frames: None or minimal (this is aggressive, not defensive)
- Stamina cost: TBD (likely 10-15)

**Tactical Use:**

- Close gap on ranged enemies
- Build momentum for high-damage attack
- Pressure defensive enemies
- Cancel into attack for combo

**Balance Considerations:**

- Should NOT have i-frames (dodge is defensive, this is offensive)
- Momentum bonus should reward the risk
- Could leave player vulnerable mid-dash
- Pairs with parry → step-forward → attack combo

**Design Pillar Alignment:**

- ✓ "Meaningful, Costly Choice" - risk position for damage
- ✓ "Player as Problem Solver" - tactical gap closer
- ✓ Complements existing options without redundancy

---

## Confirmed Design Decisions (2025-12-28)

### Parry vs Dodge Balance

**Parry (Stillness):**

- Stand your ground
- Low stamina cost (5-20)
- No momentum generation
- Counter-attack ready

**Dodge (Movement):**

- Repositioning freedom
- High stamina cost (15-35)
- Imparts momentum (away from threat)
- Breaks combat flow

**Balance Rationale:**

- Parry's stillness balances dodge's movement advantage
- Dodge momentum is defensive (escape), not offensive
- Creates tactical choice: efficient defense (parry) vs positional control (dodge)

### Attack Stamina Cost

**Decision:** Basic attacks remain **stamina-free**

**Rationale:**

- Encourages aggressive baseline play
- Stamina management focuses on defensive/mobility options
- Offensive cost comes from momentum generation systems:
  - Sprint drains stamina (future)
  - Special moves cost stamina (future)
  - Heavy attacks cost stamina (future)

**MVP Approach:**

- Free basic attacks ✓
- Momentum damage rewards movement
- Stamina pressure from defense keeps combat tense

---

*Last Updated: 2025-12-28*

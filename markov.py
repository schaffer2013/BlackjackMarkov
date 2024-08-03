# Define softness options
import csv
from functools import cache
import os
import time
from datetime import datetime, timedelta
from subset import get

import numpy as np
from combos import getAllCombos

LOSS = -1.0
PUSH = 0.0
WIN = 1.0

DECK_COUNT = 1

NO_ACE = 'NO_ACE'
SOFT = 'SOFT'
HARD = 'HARD'

FULL_DECK_STOCK = [4, 16, 4, 4, 4, 4, 4, 4, 4, 4]
FULL_DECK = np.multiply(FULL_DECK_STOCK, DECK_COUNT)
RANKS = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]

FILE_NAME = f'blackjack_ev_results_{DECK_COUNT}_decks.csv'

existing_results = []

global hitEVcount
hitEVcount = 0

noAceCount = 20  # From 2 to 21 (inclusive) 
hardCount = 10   # HARD options for 12-16
softCount = 11   # From 11 to 16 (inclusive)
TOTAL_ARRAY_LENGTH = noAceCount + softCount + hardCount + 1  # Total array length including bust
HAND_VALUE_ARRAY = [
    (2, NO_ACE), (3, NO_ACE), (4, NO_ACE), (5, NO_ACE), (6, NO_ACE),
    (7, NO_ACE), (8, NO_ACE), (9, NO_ACE), (10, NO_ACE), (11, NO_ACE),
    (12, NO_ACE), (13, NO_ACE), (14, NO_ACE), (15, NO_ACE), (16, NO_ACE),
    (17, NO_ACE), (18, NO_ACE), (19, NO_ACE), (20, NO_ACE), (21, NO_ACE),
    (11, SOFT), (12, SOFT), (13, SOFT), (14, SOFT), (15, SOFT), (16, SOFT),
    (17, SOFT), (18, SOFT), (19, SOFT), (20, SOFT), (21, SOFT), 
    (12, HARD), (13, HARD), (14, HARD), (15, HARD), (16, HARD),
    (17, HARD), (18, HARD), (19, HARD), (20, HARD), (21, HARD), 
    (22, NO_ACE)  # Bust case
]
EMPTY = [0.0] * TOTAL_ARRAY_LENGTH

if os.path.isfile(FILE_NAME):
    with open(FILE_NAME, mode='r', newline='') as file:
        csv_reader = csv.reader(file)

        # Skip the header
        next(csv_reader, None)

        # Iterate over each row in the CSV file
        for row in csv_reader:
            # Process each row
            existing_results.append(list(map(int, row[0:3])))
            #print(row)  # Or do something else with the row data

def unitTest():
    if len(HAND_VALUE_ARRAY) != TOTAL_ARRAY_LENGTH:
        raise Exception("HAND_VALUE_ARRAY length does not match TOTAL_ARRAY_LENGTH")
    
    for i in range(TOTAL_ARRAY_LENGTH):
        check = valueToArray(HAND_VALUE_ARRAY[i])
        if not check[i]:
            raise Exception(f"Test failed for HAND_VALUE_ARRAY[{i}] = {HAND_VALUE_ARRAY[i]}")
    
    print("All tests passed.")

def estimate_completion_time(start_time, percent_complete, numEvents):
    """
    Estimate the completion time given a start time and the percent completed.

    Parameters:
    start_time (datetime): The time the process started.
    percent_complete (float): The percent completion of the process (0 to 100).

    Returns:
    datetime: The estimated completion time.
    """

    if not (0 <= numEvents):
        raise ValueError("BAD")
    if not (0 <= percent_complete <= 100):
        raise ValueError("Percent complete must be between 0 and 100.")

    if percent_complete == 0:
        print("Percent complete cannot be zero.")
        return None

    current_time = datetime.now()
    elapsed_time = current_time - start_time
    estimated_total_time = elapsed_time / (percent_complete)
    estimated_completion_time = start_time + estimated_total_time
    timePerEvent = elapsed_time/numEvents
    
    return estimated_completion_time, timePerEvent

def deckToProbs(deck):
    deck_array = np.array(deck)
    total = deck_array.sum()
    return (deck_array / total).tolist()

def addLists(list1, list2):
    return np.add(list1, list2).tolist()

def scaleList(oldList, scalar):
    return np.multiply(oldList, scalar).tolist()

def valueToArray(hand_value_tuple):
    """
    Converts a blackjack hand value and softness into an array representation.
    
    Args:
    hand_value_tuple (tuple): A tuple containing the hand value and softness (NO_ACE, SOFT, HARD).
    
    Returns:
    list: An array where indices represent hand values and bust, with True indicating the current hand value.
    """
    value, softness = hand_value_tuple
    arr = np.zeros(TOTAL_ARRAY_LENGTH, dtype=bool)
    
    # If bust
    if value > 21:
        arr[-1] = True
        return arr.tolist()
    
    # Hard counts, including HARD options
    if softness == NO_ACE:
        arr[value - 2] = True
    elif softness == HARD:
        arr[(value - 12) + noAceCount + softCount] = True
    # Soft counts
    else:
        arr[(value - 11) + noAceCount] = True
    
    return arr.tolist()

def blackjack_hand_value(hand):
    """
    Calculate the value of a blackjack hand and determine its softness.
    
    Args:
    hand (list): A list of integers representing the ranks in a blackjack hand (between [2, 11]).
    
    Returns:
    tuple: A tuple containing the total value of the hand and the softness (NO_ACE, SOFT, HARD).
    """
    total_value = 0
    aces_count = 0
    softness = NO_ACE
    
    for card in hand:
        if card == 11:
            aces_count += 1
        total_value += card

    while total_value > 21 and aces_count > 0:
        total_value -= 10
        aces_count -= 1

    if aces_count > 0:
        softness = SOFT if total_value + 10 <= 21 else HARD

    return total_value, softness

def update_blackjack_hand(oldHandValue, wasSoft, newCardValue):
    """
    Update the blackjack hand value with a new card and determine its softness.
    
    Args:
    oldHandValue (int): The value of the hand before drawing the new card.
    wasSoft (str): The softness of the hand before drawing the new card (NO_ACE, SOFT, HARD).
    newCardValue (int): The value of the new card drawn (between 2 and 11).
    
    Returns:
    tuple: A tuple containing the new hand value and the softness (NO_ACE, SOFT, HARD).
    """
    if not (2 <= newCardValue <= 11):
        raise ValueError("New card value must be between 2 and 11.")

    # Calculate the new hand value
    newHandValue = oldHandValue + newCardValue
    softness = wasSoft

    # Check if the new hand is soft or hard
    if newCardValue == 11:
        if newHandValue <= 21:
            softness = SOFT
        else:
            newHandValue -= 10  # Convert the Ace from 11 to 1 if it causes a bust
            softness = HARD 
    elif wasSoft == SOFT and newHandValue > 21:
        newHandValue -= 10
        softness = HARD

    return newHandValue, softness

def arrFromHand(hand):
    value, softness = blackjack_hand_value(hand)
    return valueToArray((value, softness))

@cache
def newCardAddedToArray(oldHandValue, wasSoft, newCardValue):
    value, softness = update_blackjack_hand(oldHandValue, wasSoft, newCardValue)
    return valueToArray((value, softness))

def getRemovedCard(newValue, oldValue):
    removedCard = newValue - oldValue
    if removedCard <= 1:
        removedCard += 10
    return removedCard

def removeValFromDeck(deck, val):
    if not (2 <= val <= 11):
        raise ValueError("New card value must be between 2 and 11.")
    deck_array = np.array(deck)
    deck_array[11 - val] -= 1
    return deck_array.tolist()

def dealerHold(value, remainingDeck = FULL_DECK, isSoft = NO_ACE):
    if value >= 17:
        return valueToArray((value, isSoft))
    
    # Distribution of hand values after drawing every possible card
    runningSums = [0.0] * TOTAL_ARRAY_LENGTH
    probsToDrawCard = deckToProbs(remainingDeck)
    for rank, prob in zip(RANKS, probsToDrawCard):
        nextRankArray = newCardAddedToArray(value, isSoft, rank)
        runningSums = addLists(runningSums, scaleList(nextRankArray, prob))

    debugList = []
    for i in range(TOTAL_ARRAY_LENGTH):
        debugList.append([HAND_VALUE_ARRAY[i], runningSums[i]])

    # Using distributed hand values to give their contribution to the total
    runningTotal = EMPTY.copy()
    for i in range(TOTAL_ARRAY_LENGTH):
        if runningSums[i] > 0.0:
            newVal, newSoft = HAND_VALUE_ARRAY[i]
            removedCard = getRemovedCard(newVal, value)
            nextGen = dealerHold(newVal, isSoft = newSoft, remainingDeck= removeValFromDeck(remainingDeck, removedCard))

            runningTotal = addLists(runningTotal, scaleList(nextGen, runningSums[i]))
            #debugList = getDebugList(runningSums)
            a = 1

    return runningTotal

#def getDebugList(l):
    # debugList = []
    # for i in range(TOTAL_ARRAY_LENGTH):
    #     debugList.append([HAND_VALUE_ARRAY[i], l[i]])
    # return debugList

def dealerFinalArray(arr):
    arr = np.array(arr)
    runningArray = np.zeros(21 - 17 + 1)
    for softness in [NO_ACE, SOFT, HARD]:
        tempArr = arr[HAND_VALUE_ARRAY.index((17, softness)):HAND_VALUE_ARRAY.index((21, softness)) + 1]
        runningArray += tempArr
    runningArray = np.append(runningArray, arr[-1])
    return runningArray.tolist()

def getDealerResultFromUpcard(dealerUpcard, remainingDeck):
    softness = SOFT if dealerUpcard == 11 else NO_ACE
    dealerResult = dealerHold(dealerUpcard, remainingDeck, isSoft= softness)
    return dealerResult

def checkStayEV(playerHandValue, dealerUpcard, remainingDeck):

    dealerResult = getDealerResultFromUpcard(dealerUpcard, remainingDeck)
    finalArr = dealerFinalArray(dealerResult)
    # finalArr is chances for 17, 18, 19, 20, 21 and bust
    if playerHandValue < 17:
        return (sum(finalArr[0:5]) * LOSS + finalArr[-1] * WIN)
    if playerHandValue > 21:
        return LOSS
    ev = 0
    for val in range(17, 22 + 1):
        prob = finalArr[val - 17]
        if val < playerHandValue or val > 21:
            result = WIN
        elif val == playerHandValue:
            result = PUSH
        else:
            result = LOSS
        ev += prob * result
    return ev

def checkHitEV(playerHandValue, dealerUpcard, isSoft = NO_ACE, remainingDeck = FULL_DECK):
    global hitEVcount
    hitEVcount += 1
    if hitEVcount % 10000 == 0:
        #estimated_time, timePerEvent = estimate_completion_time(start_datetime, (hitEVcount - lastCount)/74239, (hitEVcount - lastCount))
        #print(f"Current time: {datetime.now()} Estimated completion time: {estimated_time} Time per event: {timePerEvent}")
        print(f"Current time: {datetime.now()}")
        print(hitEVcount)

    HIT = 1
    STAY = 0

    if playerHandValue > 21:
        return LOSS, STAY, 1

    runningSums = [0.0] * TOTAL_ARRAY_LENGTH
    probsToDrawCard = deckToProbs(remainingDeck)
    for rank, prob in zip(RANKS, probsToDrawCard):
        nextRankArray = newCardAddedToArray(playerHandValue, isSoft, rank)
        runningSums = addLists(runningSums, scaleList(nextRankArray, prob))
    #debugList = getDebugList(runningSums)

    runningTotalEV = 0.0

    totalCallCount = 1
    for i in range(TOTAL_ARRAY_LENGTH):
        if runningSums[i] > 0.0:
            newVal, newSoft = HAND_VALUE_ARRAY[i]
            removedCard = getRemovedCard(newVal, playerHandValue)
            nextGen, _, callCount = checkHitEV(newVal, dealerUpcard, isSoft = newSoft, remainingDeck= removeValFromDeck(remainingDeck, removedCard))
            totalCallCount += callCount

            runningTotalEV += nextGen * runningSums[i]
            #debugList = getDebugList(runningTotal)
            a = 1
    hitEV = runningTotalEV
    stayEV = checkStayEV(playerHandValue, dealerUpcard, remainingDeck)


    bestEV = max(hitEV, stayEV)
    if stayEV >= hitEV:
        bestDecision = STAY
    else:
        bestDecision = HIT

    return bestEV, bestDecision, totalCallCount

    a = 1
        

# Run unit tests
unitTest()

total_start = time.time()

possibleCombos = []
typicalRange = range(2, 11+1)
for i in typicalRange:
    for j in typicalRange:
        for k in typicalRange:
            if j >= i:
                possibleCombos.append([i, j, k])

combosAndOcc = getAllCombos(DECK_COUNT)

potentialResults = get()
potentialResults.reverse()
for c in existing_results:
    if tuple(c) in potentialResults:
        potentialResults.remove(tuple(c))
    else:
        print(f"{c} not found")

#testCombosRemaining = get()

if not os.path.isfile(FILE_NAME):
# Open CSV file for writing
    with open(FILE_NAME, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write headers
        writer.writerow(['Player Low Card', 'Player High Card', 'Dealer Upcard', 'EV_hit', 'Best Decision', 'time(s)', 'Recursive Calls', 'Occurrences'])

for playerLowCard, playerHighCard, dealerUpcard in potentialResults:
    print(f"{playerLowCard}, {playerHighCard}, {dealerUpcard} evaluated.")
    combo = [playerLowCard, playerHighCard, dealerUpcard]
    # if combo in potentialResults:
    #     print (f"{combo} founds and skipped")
    #     break

    start = time.time()
    global start_datetime
    start_datetime = datetime.now()
    global lastCount
    lastCount = hitEVcount
    playerHand = [playerLowCard, playerHighCard]

    playerVal, playerSoft = blackjack_hand_value(playerHand)

    deck = FULL_DECK.copy()
    deck = removeValFromDeck(deck, dealerUpcard)
    for c in playerHand:
        deck = removeValFromDeck(deck, c)

    EV_hit = checkHitEV(playerVal, dealerUpcard, playerSoft)
    elapsed = time.time() - start
    #print(f"Completed in {elapsed} seconds.")

    # Write to CSV file
    with open(FILE_NAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        bestMove = 'HIT' if EV_hit[1] else 'STAY'
        for c in combosAndOcc:
            if (playerLowCard, playerHighCard, dealerUpcard) == c[0:3]:
                occ = c[3]
                break
        writer.writerow([playerLowCard, playerHighCard, dealerUpcard, EV_hit[0], bestMove, elapsed, EV_hit[2], occ])

        print(f"{elapsed} seconds")

total_elapsed = time.time() - total_start
print(f"Completed in {total_elapsed} seconds.")
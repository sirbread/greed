let gameStarted = false;
let startTime = null;
let pregameInterval = null;
let lastRoundId = null;
let didInitialPrefill = false;
let isSubmitting = false;
let lastSubmittedValue = null;
let winnerAnnounced = false;
let gameEnded = false;
let currentUser = null;
let currentToken = null;
let usernameSet = false;
let pregameActive = false; 
let roundStatusTimeout = null;
let roundTimerInterval = null;
let roundTimeLeft = 0;

function formatCountdown(ms) {
    let s = Math.max(0, Math.floor(ms/1000));
    let d = Math.floor(s/86400);
    s = s % 86400;
    let h = Math.floor(s/3600);
    s = s % 3600;
    let m = Math.floor(s/60);
    s = s % 60;
    return `${d} day${d!==1?'s':''} ${h} hour${h!==1?'s':''} ${m} minute${m!==1?'s':''} ${s} second${s!==1?'s':''}`;
}

function updateGreedRate() {
    if (!currentUser) {
        document.getElementById("greed-rate").textContent = "";
        return;
    }
    currentUser.getIdToken().then(token => {
        fetch("/greed_rate/", {
            headers: {
                "Authorization": "Bearer " + token
            }
        })
        .then(res => res.json())
        .then(data => {
            if (typeof data.greed_rate === "number") {
                document.getElementById("greed-rate").textContent =
                    `your greed rate: ${data.greed_rate.toFixed(2)}`;
                document.getElementById('greedDiss').innerText = 
                    data.diss;
            } else {
                document.getElementById("greed-rate").textContent = "";
            }
        });
    });
}

fetch("/start_time/")
    .then(res => res.json())
    .then(data => {
        startTime = new Date(data.start_time);
        checkPregameState();
    }).catch(() => {
        document.getElementById("pregame-container").style.display = "none";
        document.getElementById("main-content").style.display = "";
        pregameActive = false;
    });

function checkPregameState() {
    const now = new Date();
    if (startTime && now < startTime) {
        pregameActive = true;
        document.getElementById("pregame-container").style.display = "block";
        document.getElementById("main-content").style.display = "none";
        updatePregameUserInfo();
        updatePregameTimer();
        updatePregameUsernameSection();
    } else {
        pregameActive = false;
        document.getElementById("pregame-container").style.display = "none";
        document.getElementById("main-content").style.display = "";
    }
}

function updatePregameUserInfo() {
    document.getElementById("pregame-userinfo").textContent = document.getElementById("user-info").textContent;
    document.getElementById("pregame-logout").style.display =
        document.getElementById("logout").style.display === "inline-block" ? "inline-block" : "none";
}

function updatePregameUsernameSection() {
    if (!usernameSet && currentUser) {
        document.getElementById("pregame-username-section").style.display = "block";
    } else {
        document.getElementById("pregame-username-section").style.display = "none";
    }
}

function updatePregameTimer() {
    const timerElem = document.getElementById("pregame-timer");
    if (pregameInterval) clearInterval(pregameInterval);
    function tick() {
        const now = new Date();
        const diff = startTime - now;
        if (diff > 0) {
            timerElem.textContent = formatCountdown(diff);
        } else {
            timerElem.textContent = "starting...";
            clearInterval(pregameInterval);
            setTimeout(() => location.reload(), 1200);
        }
    }
    tick();
    pregameInterval = setInterval(tick, 1000);
}

document.getElementById('pregame-logout').onclick = function() {
    auth.signOut();
};

document.getElementById('logout').onclick = function() {
    auth.signOut();
};

function showUsernameSection() {
    if (!pregameActive) {
        document.getElementById("username-section").style.display = "block";
        document.getElementById("game").style.display = "none";
    }
}
function hideUsernameSection() {
    if (!pregameActive) {
        document.getElementById("username-section").style.display = "none";
        document.getElementById("game").style.display = "block";
    }
}

function checkIfUsernameSet(token) {
    return fetch("/whoami/", {
        method: "GET",
        headers: {"Authorization": "Bearer " + token}
    })
    .then(res => res.ok ? res.json() : Promise.reject())
    .then(data => !!data.username)
    .catch(() => false);
}

function checkAuthAndUsernameOrRedirect() {
    if (!currentUser) {
        window.location.href = '/login';
        return;
    }
    currentUser.getIdToken().then(token => {
        fetch("/whoami/", {
            method: "GET",
            headers: {"Authorization": "Bearer " + token}
        })
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(data => {
            if (!data.username) {
                window.location.href = '/login';
            }
        })
        .catch(() => {
            window.location.href = '/login';
        });
    });
}

auth.onAuthStateChanged(user => {
    currentUser = user;
    if (!user) {
        window.location.href = '/login';
        return;
    }
    document.getElementById('logout').style.display = 'inline-block';
    user.getIdToken().then(token => {
        currentToken = token;
        fetch("/whoami/", {
            method: "GET",
            headers: {"Authorization": "Bearer " + token}
        })
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(data => {
            const username = data.username;
            const googleName = user.displayName || user.email;
            const userInfoDiv = document.getElementById('user-info');
            if (username && googleName) {
                userInfoDiv.textContent = `hello ${username}! you're logged in as ${googleName}.`;
            } else if (googleName) {
                userInfoDiv.textContent = `welcome to greed! you're logged in as ${googleName}`;
            } else {
                userInfoDiv.textContent = "";
            }
            usernameSet = !!data.username;
            updatePregameUserInfo();
            updatePregameUsernameSection();
            if (!usernameSet) {
                window.location.href = '/login';
            } else if (!pregameActive) {
                hideUsernameSection();
            }
            updateGreedRate();
            pollAwaitingSubmission(); 
        })
        .catch(() => {
            document.getElementById('user-info').textContent = "";
            usernameSet = false;
            window.location.href = '/login';
        });
    });
});

//fo pre game gng
document.getElementById("pregame-username-go").onclick = function() {
    const username = document.getElementById("pregame-username-input").value.trim();
    const errorDiv = document.getElementById("pregame-username-error");
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        errorDiv.textContent = "invalid username (letters, numbers, dashes, underscores only)";
        return;
    }
    if (username.length < 2 || username.length > 20) {
        errorDiv.textContent = "username must be 2-20 characters";
        return;
    }
    errorDiv.textContent = "";
    fetch("/set_username/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + currentToken
        },
        body: JSON.stringify({username})
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            usernameSet = true;
            const googleName = currentUser.displayName || currentUser.email;
            document.getElementById('user-info').textContent =
                `hello ${username}! you're logged in as ${googleName}.`;
            updatePregameUserInfo();
            updatePregameUsernameSection();
            updateGreedRate();
            pollAwaitingSubmission();
        } else if (data.error === "taken") {
            errorDiv.textContent = "this username is taken gng";
        } else if (data.error === "invalid") {
            errorDiv.textContent = "invalid username gng (letters/numbers/underscores only)";
        } else {
            errorDiv.textContent = "some thing happened, your thing didn't happen though ";
        }
    })
    .catch(() => {
        errorDiv.textContent = "the server is cooked gng ";
    });
};

//for main game gng \/
document.getElementById("username-go").onclick = function() {
    const username = document.getElementById("username-input").value.trim();
    const errorDiv = document.getElementById("username-error");
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        errorDiv.textContent = "invalid username (letters, numbers, dashes, underscores only)";
        return;
    }
    if (username.length < 2 || username.length > 20) {
        errorDiv.textContent = "username must be 2-20 characters";
        return;
    }
    errorDiv.textContent = "";
    fetch("/set_username/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + currentToken
        },
        body: JSON.stringify({username})
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            hideUsernameSection();
            usernameSet = true;
            const googleName = currentUser.displayName || currentUser.email;
            document.getElementById('user-info').textContent =
                `hello ${document.getElementById("username-input").value.trim()}! you're logged in as ${googleName}.`;
            updatePregameUserInfo();
            updatePregameUsernameSection();
            updateGreedRate();
            pollAwaitingSubmission();
        } else if (data.error === "taken") {
            errorDiv.textContent = "this username is taken gng";
        } else if (data.error === "invalid") {
            errorDiv.textContent = "invalid username gng (letters/numbers/underscores only)";
        } else {
            errorDiv.textContent = "some thing happened, your thing didn't happen though ";
        }
    })
    .catch(() => {
        errorDiv.textContent = "the server is cooked gng ";
    });
};

function submit() {
    const value = parseInt(document.getElementById("numberInput").value);
    const inputMsgDiv = document.getElementById("input-message");
    const statusDiv = document.getElementById("status");
    if (!currentUser) {
        inputMsgDiv.textContent = "please sign in first.";
        return;
    }
    if (!usernameSet) {
        inputMsgDiv.textContent = "please set your username first";
        return;
    }
    if (isNaN(value) || value < 1 || value > 10) {
        inputMsgDiv.textContent = "please enter a number from 1 to 10";
        return;
    }
    inputMsgDiv.textContent = "";

    isSubmitting = true;
    lastSubmittedValue = value;
    statusDiv.textContent = "submitting...";
    statusDiv.classList.add("status-in-transit");

    currentUser.getIdToken(true).then(token => {
        currentToken = token;
        fetch("/submit/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({
                number_selected: value
            })
        })
        .then(res => res.json())
        .then(() => {
            document.getElementById("numberInput").value = value;
            updateGreedRate();
            pollAwaitingSubmission();
        })
    });
}

function loadScores() {
    fetch("/scores/")
        .then(res => res.json())
        .then(scores => {
            if (scores.length === 0) {
                document.getElementById("scores").textContent = "no scores yet."
                return
            }
            document.getElementById("scores").textContent =
                scores.map((s, i) => `${i+1}. ${s.user_name}: ${s.total_score.toFixed(2)}`).join("\n")
        })
}

function startLocalRoundTimer(initialSeconds) {
    if (roundTimerInterval) clearInterval(roundTimerInterval);
    roundTimeLeft = initialSeconds;
    updateTimerDisplay(roundTimeLeft);
    roundTimerInterval = setInterval(() => {
        if (gameEnded) {
            clearInterval(roundTimerInterval);
            return;
        }
        roundTimeLeft--;
        if (roundTimeLeft < 0) {
            clearInterval(roundTimerInterval);
        } else {
            updateTimerDisplay(roundTimeLeft);
        }
    }, 1000);
}

function updateTimerDisplay(secondsLeft) {
    let timerDiv = document.getElementById("timer");
    if (gameEnded) {
        timerDiv.textContent = "timer: ENDED";
        return;
    }
    let min = Math.floor(secondsLeft / 60);
    let sec = secondsLeft % 60;
    timerDiv.textContent = `time left this round: ${min}:${sec.toString().padStart(2, '0')}`;
}

function checkRoundStatus() {
    if (pregameActive || gameEnded) return;
    fetch("/round/")
        .then(res => res.json())
        .then(data => {
            startLocalRoundTimer(data.time_left_seconds || 0);
            if (lastRoundId !== data.round_id) {
                lastRoundId = data.round_id;
                loadScores();
                document.getElementById("numberInput").value = "";
                document.getElementById("status").textContent = "";
                document.getElementById("status").classList.remove("status-in-transit");
                document.getElementById("input-message").textContent = "";
                didInitialPrefill = false;
                isSubmitting = false;
                lastSubmittedValue = null;
                checkForWinner();
                updateGreedRate();
            }
            scheduleNextRoundPoll(data.time_left_seconds || 0);
        });
}

function scheduleNextRoundPoll(timeLeftSeconds) {
    if (roundStatusTimeout) clearTimeout(roundStatusTimeout);
    let nextPoll = Math.max(timeLeftSeconds - 1, 2);
    roundStatusTimeout = setTimeout(checkRoundStatus, nextPoll * 1000);
}

function checkForWinner() {
    if (pregameActive) return;
    fetch("/winner/")
        .then(res => res.json())
        .then(data => {
            if (data.winner && !winnerAnnounced) {
                winnerAnnounced = true;
                gameEnded = true;
                showWinner(data.user_name, data.user_id, data.score);
                updateTimerDisplay(0); 
            }
        });
}

function showWinner(name, id, score) {
    const gameDiv = document.getElementById("game");
    gameDiv.innerHTML = `<div class="winner-message">
    congratulations <b>${name}</b> (ID: ${id})!<br>
    you won with a score of ${score}.
    </div>`;
}

function pollAwaitingSubmission() {
    if (pregameActive || gameEnded || !currentUser) return;
    currentUser.getIdToken().then(token => {
        fetch("/awaiting/", {
            headers: {
                "Authorization": "Bearer " + token
            }
        })
        .then(res => res.json())
        .then(data => {
            const statusDiv = document.getElementById("status");
            if (data && data.number_selected !== undefined) {
                if (isSubmitting) { 
                    if (data.number_selected === lastSubmittedValue) {
                        isSubmitting = false;
                        statusDiv.textContent = "submitted number: " + data.number_selected;
                        statusDiv.classList.remove("status-in-transit");
                    } else {
                        statusDiv.textContent = "submitting...";
                        statusDiv.classList.add("status-in-transit");
                    }
                } else {
                    statusDiv.textContent = "submitted number: " + data.number_selected;
                    statusDiv.classList.remove("status-in-transit");
                }
                if (!didInitialPrefill) {
                    document.getElementById("numberInput").value = data.number_selected;
                    didInitialPrefill = true;
                }
            } else {
                statusDiv.textContent = "";
                statusDiv.classList.remove("status-in-transit");
            }
        });
    });
}

function prefillAwaitingSubmission() {
    didInitialPrefill = false;
    pollAwaitingSubmission();
}

function formatDuration(seconds) {
    let parts = [];
    let h = Math.floor(seconds / 3600);
    let m = Math.floor((seconds % 3600) / 60);
    let s = seconds % 60;
    if (h > 0) parts.push(h + " hour" + (h !== 1 ? "s" : ""));
    if (m > 0) parts.push(m + " minute" + (m !== 1 ? "s" : ""));
    if (s > 0) parts.push(s + " second" + (s !== 1 ? "s" : ""));
    return parts.join(", ");
}
function setRoundDurationDesc() {
    fetch("/config/")
        .then(res => res.json())
        .then(cfg => {
            let desc = formatDuration(cfg.round_duration_seconds);
            document.getElementById("round-duration-desc").textContent =
                "each round lasts: " + desc + ".";
        });
}
setRoundDurationDesc();

loadScores();
checkRoundStatus();
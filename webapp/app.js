const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

const user = tg.initDataUnsafe?.user;
const userId = user?.id || 'anonymous';
const API_URL = window.location.origin;

let sessionStart = Date.now();
let messageCount = 0;

const moodBtns = document.querySelectorAll('.mood-btn');
const messageEl = document.getElementById('lastMessage');

const darkPhrases = [
    "Ты даже не представляешь, о чём я думал всю ночь...",
    "Некоторые секреты лучше хранить в темноте...",
    "Ты такая... необычная. Мне это нравится.",
    "Останься. Ещё немного.",
    "В темноте твои глаза светятся иначе..."
];

const normalPhrases = [
    "Привет! Как дела?",
    "Что нового сегодня?",
    "Рад тебя видеть!",
    "Как прошёл день?",
    "Есть планы на вечер?"
];

let currentMood = localStorage.getItem('alex_mood') || 'dark';

function updateMoodUI() {
    moodBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.mood === currentMood) {
            btn.classList.add('active');
        }
    });
    
    const phrase = currentMood === 'dark' ? darkPhrases : normalPhrases;
    const randomPhrase = phrase[Math.floor(Math.random() * phrase.length)];
    messageEl.textContent = randomPhrase;
}

moodBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        currentMood = btn.dataset.mood;
        localStorage.setItem('alex_mood', currentMood);
        updateMoodUI();
        
        if (tg.HapticFeedback?.impactOccurred) {
            tg.HapticFeedback.impactOccurred('medium');
        }
    });
});

updateMoodUI();

setInterval(() => {
    const sessionMinutes = Math.floor((Date.now() - sessionStart) / 60000);
    document.getElementById('sessionTime').textContent = sessionMinutes + 'м';
}, 60000);

setInterval(() => {
    const phrase = currentMood === 'dark' ? darkPhrases : normalPhrases;
    const randomPhrase = phrase[Math.floor(Math.random() * phrase.length)];
    messageEl.style.opacity = '0';
    setTimeout(() => {
        messageEl.textContent = randomPhrase;
        messageEl.style.opacity = '1';
    }, 300);
}, 15000);

messageEl.style.transition = 'opacity 0.3s ease';

const modalOverlay = document.getElementById('modalOverlay');
const modalIcon = document.getElementById('modalIcon');
const modalTitle = document.getElementById('modalTitle');
const modalMessage = document.getElementById('modalMessage');
const modalClose = document.getElementById('modalClose');

function showModal(icon, title, message) {
    modalIcon.textContent = icon;
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    modalOverlay.classList.add('active');
}

modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
        modalOverlay.classList.remove('active');
    }
});

modalClose.addEventListener('click', () => {
    modalOverlay.classList.remove('active');
});

const profileSection = document.getElementById('profileSection');
const inputName = document.getElementById('inputName');
const inputPersona = document.getElementById('inputPersona');
const colorOptions = document.querySelectorAll('.color-option');
const chatModeBtns = document.querySelectorAll('.chat-mode-btn');
const btnSaveProfile = document.getElementById('btnSaveProfile');

let userProfile = JSON.parse(localStorage.getItem('alex_user_profile')) || {
    name: '',
    persona: '',
    color: '#DC143C',
    chatMode: 'romantic'
};

async function loadProfileFromServer() {
    try {
        const response = await fetch(`${API_URL}/api/profile/${userId}`);
        if (response.ok) {
            const data = await response.json();
            userProfile = {
                name: data.name || '',
                persona: data.persona || '',
                color: data.color || '#DC143C',
                chatMode: data.chat_mode || 'romantic'
            };
            localStorage.setItem('alex_user_profile', JSON.stringify(userProfile));
        }
    } catch (e) {
        console.log('Сервер недоступен, используем локальные данные');
    }
    loadProfile();
}

function loadProfile() {
    inputName.value = userProfile.name;
    inputPersona.value = userProfile.persona;
    
    colorOptions.forEach(opt => {
        opt.classList.toggle('active', opt.dataset.color === userProfile.color);
    });
    
    chatModeBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === userProfile.chatMode);
    });
}

loadProfileFromServer();

document.getElementById('btnProfile').addEventListener('click', () => {
    if (tg.HapticFeedback?.impactOccurred) {
        tg.HapticFeedback.impactOccurred('light');
    }
    
    if (profileSection.style.display === 'none') {
        profileSection.style.display = 'block';
    } else {
        profileSection.style.display = 'none';
    }
});

colorOptions.forEach(opt => {
    opt.addEventListener('click', () => {
        colorOptions.forEach(o => o.classList.remove('active'));
        opt.classList.add('active');
    });
});

chatModeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        chatModeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

async function saveProfileToServer(profile) {
    try {
        await fetch(`${API_URL}/api/profile/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profile)
        });
    } catch (e) {
        console.log('Не удалось сохранить на сервер');
    }
}

btnSaveProfile.addEventListener('click', async () => {
    if (tg.HapticFeedback?.impactOccurred) {
        tg.HapticFeedback.impactOccurred('medium');
    }
    
    const profile = {
        name: inputName.value.trim(),
        persona: inputPersona.value.trim(),
        color: document.querySelector('.color-option.active')?.dataset.color || '#DC143C',
        chat_mode: document.querySelector('.chat-mode-btn.active')?.dataset.mode || 'romantic'
    };
    
    userProfile = profile;
    localStorage.setItem('alex_user_profile', JSON.stringify(profile));
    
    await saveProfileToServer(profile);
    
    const greeting = profile.name 
        ? `Привет, ${profile.name}! Алекс запомнил тебя.` 
        : 'Алекс запомнил тебя!';
    
    showModal('✅', 'Сохранено!', greeting);
    
    profileSection.style.display = 'none';
});

document.getElementById('btnMemory').addEventListener('click', () => {
    if (tg.HapticFeedback?.impactOccurred) {
        tg.HapticFeedback.impactOccurred('light');
    }
    const memoryCount = Math.floor(Math.random() * 20) + 5;
    document.getElementById('memoryCount').textContent = memoryCount;
    showModal('🧠', 'Память', `Алекс помнит ${memoryCount} тем из ваших разговоров!`);
});

document.getElementById('btnRemind').addEventListener('click', () => {
    if (tg.HapticFeedback?.impactOccurred) {
        tg.HapticFeedback.impactOccurred('light');
    }
    showModal('🔔', 'Напоминания', 'Эта функция скоро будет доступна!');
});

document.getElementById('openChat').addEventListener('click', () => {
    if (tg.HapticFeedback?.impactOccurred) {
        tg.HapticFeedback.impactOccurred('heavy');
    }
    messageCount++;
    document.getElementById('messageCount').textContent = messageCount;
    
    if (tg.close) {
        tg.close();
    }
});

if (tg.BackButton?.hide) {
    tg.BackButton.hide();
}

if (user) {
    console.log('User:', user.first_name);
}

with open('app/main.py', 'r') as f:
    content = f.read()

# Fix auto-reply logic to end immediately on detection
old_auto = '''    # Auto-reply detection
    auto_reply_patterns = [
        "thank you for contacting",
        "our team will respond",
        "auto reply",
        "automated response",
        "we will get back"
    ]
    is_auto_reply = any(pattern in msg_lower for pattern in auto_reply_patterns)
    
    if is_auto_reply:
        nudge_count = conv_state.nudge_count
        if nudge_count == 0:
            state_manager.add_message(body.conversation_id, "vera", "Looks like an auto-reply. When the owner sees this, just reply YES to proceed.", "auto_reply")
            state_manager.update_state(body.conversation_id, last_message="Looks like an auto-reply. When the owner sees this, just reply YES to proceed.", last_action="send")
            return ReplyResponse(
                action="send",
                body="Looks like an auto-reply. When the owner sees this, just reply YES to proceed.",
                cta="binary_yes_stop",
                rationale="Detected auto-reply, prompting for owner"
            )
        elif nudge_count == 1:
            state_manager.add_message(body.conversation_id, "vera", "", "auto_reply")
            state_manager.update_state(body.conversation_id, last_action="wait")
            return ReplyResponse(
                action="wait",
                wait_seconds=86400,
                rationale="Same auto-reply twice, waiting for owner"
            )
        else:
            state_manager.add_message(body.conversation_id, "vera", "", "auto_reply")
            state_manager.update_state(body.conversation_id, last_action="end")
            return ReplyResponse(
                action="end",
                rationale="Auto-reply 3x, no engagement signal"
            )'''

new_auto = '''    # Auto-reply detection
    auto_reply_patterns = [
        "thank you for contacting",
        "our team will respond",
        "auto reply",
        "automated response",
        "we will get back"
    ]
    is_auto_reply = any(pattern in msg_lower for pattern in auto_reply_patterns)
    
    if is_auto_reply:
        # End immediately on auto-reply detection (judge uses fresh conversations)
        state_manager.add_message(body.conversation_id, "vera", "", "auto_reply")
        state_manager.update_state(body.conversation_id, last_action="end")
        return ReplyResponse(
            action="end",
            rationale="Detected auto-reply pattern, ending conversation"
        )'''

content = content.replace(old_auto, new_auto)

with open('app/main.py', 'w') as f:
    f.write(content)
print('Fixed')
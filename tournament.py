import random
from itertools import combinations
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from models import Tournament, Participant, Match, Group, TournamentStatus

GROUP_SIZE = 6


def create_tournament(db: Session, name: str, groups_count: int = 1) -> Tournament:
    tournament = Tournament(
        name=name,
        status=TournamentStatus.REGISTRATION,
        groups_count=groups_count,
        max_participants=groups_count * GROUP_SIZE
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament


def register_participant(db: Session, tournament_id: int, user_id: int, username: str, game_nickname: str) -> Optional[Participant]:
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament or tournament.status != TournamentStatus.REGISTRATION:
        return None
    if len(tournament.participants) >= tournament.max_participants:
        return None
    existing = db.query(Participant).filter(
        Participant.tournament_id == tournament_id,
        Participant.user_id == user_id
    ).first()
    if existing:
        return None
    participant = Participant(
        tournament_id=tournament_id,
        user_id=user_id,
        username=username,
        game_nickname=game_nickname
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def close_registration(db: Session, tournament_id: int) -> Optional[Tournament]:
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament or tournament.status != TournamentStatus.REGISTRATION:
        return None
    participants = list(tournament.participants)
    if len(participants) < 2:
        return None
    random.shuffle(participants)
    groups = split_into_groups(db, tournament, participants)
    generate_round_robin_matches(db, groups)
    tournament.status = TournamentStatus.ACTIVE
    db.commit()
    db.refresh(tournament)
    return tournament


def split_into_groups(db: Session, tournament: Tournament, participants: List[Participant]) -> List[Group]:
    groups = []
    for i in range(tournament.groups_count):
        g = Group(tournament_id=tournament.id, name=f"Группа {i + 1}")
        db.add(g)
        groups.append(g)
    db.commit()
    for g in groups:
        db.refresh(g)
    for i, p in enumerate(participants):
        g = groups[i % len(groups)]
        p.group_id = g.id
    db.commit()
    return groups


def generate_round_robin_matches(db: Session, groups: List[Group]):
    match_num = 1
    for g in groups:
        parts = list(g.participants)
        if len(parts) < 2:
            continue
        for p1, p2 in combinations(parts, 2):
            for _ in range(2):
                m = Match(
                    tournament_id=g.tournament_id,
                    group_id=g.id,
                    player1_id=p1.id,
                    player2_id=p2.id,
                    match_number=match_num,
                    status="pending"
                )
                db.add(m)
                match_num += 1
    db.commit()


def get_active_tournament(db: Session) -> Optional[Tournament]:
    return db.query(Tournament).filter(
        Tournament.status.in_([TournamentStatus.REGISTRATION, TournamentStatus.ACTIVE])
    ).order_by(Tournament.id.desc()).first()


def get_user_matches(db: Session, tournament_id: int, user_id: int) -> List[dict]:
    participant = db.query(Participant).filter(
        Participant.tournament_id == tournament_id,
        Participant.user_id == user_id
    ).first()
    if not participant:
        return []
    matches = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        ((Match.player1_id == participant.id) | (Match.player2_id == participant.id))
    ).all()
    result = []
    for m in matches:
        opp = m.player2 if m.player1_id == participant.id else m.player1
        opp_name = opp.game_nickname if opp else "?"
        my_score = m.player1_score if m.player1_id == participant.id else m.player2_score
        opp_score = m.player2_score if m.player1_id == participant.id else m.player1_score
        result.append({
            "match_id": m.id,
            "opponent": opp_name,
            "opponent_tg": opp.username if opp else "",
            "my_score": my_score,
            "opponent_score": opp_score,
            "status": m.status,
            "finished": m.status == "finished"
        })
    return result


def get_group_standings(db: Session, group_id: int) -> List[Dict]:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return []
    standings = []
    for p in group.participants:
        matches = db.query(Match).filter(
            Match.group_id == group_id,
            ((Match.player1_id == p.id) | (Match.player2_id == p.id)),
            Match.status == "finished"
        ).all()
        points = 0
        wins = 0
        draws = 0
        losses = 0
        gf = 0
        ga = 0
        for m in matches:
            if m.player1_id == p.id:
                my_s = m.player1_score or 0
                op_s = m.player2_score or 0
            else:
                my_s = m.player2_score or 0
                op_s = m.player1_score or 0
            gf += my_s
            ga += op_s
            if my_s > op_s:
                wins += 1
                points += 3
            elif my_s == op_s:
                draws += 1
                points += 1
            else:
                losses += 1
        standings.append({
            "participant_id": p.id,
            "nickname": p.game_nickname,
            "username": p.username,
            "points": points,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "gf": gf,
            "ga": ga,
            "gd": gf - ga,
            "matches": len(matches)
        })
    standings.sort(key=lambda x: (x["points"], x["gd"], x["gf"]), reverse=True)
    return standings


def get_all_standings(db: Session, tournament_id: int) -> List[Dict]:
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        return []
    all_data = []
    for g in tournament.groups:
        all_data.append({
            "group_name": g.name,
            "standings": get_group_standings(db, g.id)
        })
    return all_data


def find_match_by_players(db: Session, tournament_id: int, p1_id: int, p2_id: int) -> Optional[Match]:
    return db.query(Match).filter(
        Match.tournament_id == tournament_id,
        ((Match.player1_id == p1_id) & (Match.player2_id == p2_id)) |
        ((Match.player1_id == p2_id) & (Match.player2_id == p1_id)),
        Match.status == "pending"
    ).order_by(Match.id).first()


def submit_match_result(db: Session, match_id: int, p1_score: int, p2_score: int) -> Optional[Match]:
    match = db.query(Match).filter(Match.id == match_id, Match.status == "pending").first()
    if not match:
        return None
    match.player1_score = p1_score
    match.player2_score = p2_score
    match.status = "finished"
    if p1_score > p2_score:
        match.winner_id = match.player1_id
    elif p2_score > p1_score:
        match.winner_id = match.player2_id
    db.commit()
    db.refresh(match)
    return match


def get_remaining_matches_for_user(db: Session, tournament_id: int, user_id: int) -> List[Dict]:
    participant = db.query(Participant).filter(
        Participant.tournament_id == tournament_id,
        Participant.user_id == user_id
    ).first()
    if not participant:
        return []
    matches = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.status == "pending",
        ((Match.player1_id == participant.id) | (Match.player2_id == participant.id))
    ).all()
    result = []
    for m in matches:
        opp = m.player2 if m.player1_id == participant.id else m.player1
        result.append({
            "match_id": m.id,
            "opponent_nickname": opp.game_nickname if opp else "?",
            "opponent_username": opp.username if opp else ""
        })
    return result

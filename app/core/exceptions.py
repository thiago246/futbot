from fastapi import Request
from fastapi.responses import JSONResponse

class EmailAlreadyExistsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class BehaviorNotFoundError(Exception):
    pass

class AttributeOutOfRangeError(Exception):
    pass

class AttributeSumInvalidError(Exception):
    pass

class InvalidFormationError(Exception):
    pass

class InsufficientPlayersError(Exception):
    pass

class DuplicatePlayersError(Exception):
    pass

class PlayerNotInClubError(Exception):
    pass

class BehaviorNotAvailableError(Exception):
    pass

class SquadNotConfiguredError(Exception):
    pass

class MinTeamsTooLowError(Exception):
    pass

class EmptyLeaguePasswordError(Exception):
    pass

class InvalidLeaguePasswordError(Exception):
    pass

class LeagueFullError(Exception):
    pass

class LeagueAlreadyStartedError(Exception):
    pass

class AlreadyInLeagueError(Exception):
    pass

class LeagueNotFoundError(Exception):
    pass

class MatchDurationNotAllowed(Exception):
    pass

class NotInLeagueError(Exception):
    pass

class AlreadyPlayedMatchesError(Exception):
    pass

class BehaviorError(Exception):
    pass

class BehaviorInUseError(Exception):
    pass

class InvalidDurationError(Exception):
    pass

class SquadRequiredError(Exception):
    """Plantilla default para crear/unirse/iniciar un amistoso (422).
    Distinta de SquadNotConfiguredError, que GET /clubs/me/squad devuelve como 404."""
    pass

class FriendlyNotFoundError(Exception):
    pass

class MatchFullError(Exception):
    pass

class MatchNotAvailableError(Exception):
    pass

class CannotJoinOwnMatchError(Exception):
    pass

class MaxTeamsTooLowError(Exception):
    pass

class NotMatchCreatorError(Exception):
    pass

class MatchNotReadyError(Exception):
    pass

class MatchAlreadyStartedError(Exception):
    pass

def register_exception_handlers(app):
    @app.exception_handler(EmailAlreadyExistsError)
    def handle_email_exists(request: Request, exc: EmailAlreadyExistsError):
        return JSONResponse(status_code=409, content={"error": {"code": "EMAIL_ALREADY_EXISTS", "message": "Email already registered"}})

    @app.exception_handler(InvalidCredentialsError)
    def handle_invalid_credentials(request: Request, exc: InvalidCredentialsError):
        return JSONResponse(status_code=401, content={"error": {"code": "INVALID_CREDENTIALS", "message": "Incorrect email or password"}})

    @app.exception_handler(BehaviorNotFoundError)
    def handle_behavior_not_found(request: Request, exc: BehaviorNotFoundError):
        return JSONResponse(status_code=404, content={"error": {"code": "BEHAVIOR_NOT_FOUND", "message": "Comportamiento no encontrado"}})

    @app.exception_handler(AttributeOutOfRangeError)
    def handle_attribute_out_of_range(request: Request, exc: AttributeOutOfRangeError):
        return JSONResponse(status_code=422, content={"error": {"code": "ATTRIBUTE_OUT_OF_RANGE", "message": "Each stat must be between 20 and 100"}})

    @app.exception_handler(AttributeSumInvalidError)
    def handle_attribute_sum_invalid(request: Request, exc: AttributeSumInvalidError):
        return JSONResponse(status_code=422, content={"error": {"code": "ATTRIBUTE_SUM_INVALID", "message": "The sum of the 5 stats must be exactly 300"}})

    @app.exception_handler(MinTeamsTooLowError)
    def handle_min_teams_too_low(request: Request, exc: MinTeamsTooLowError):
        return JSONResponse(status_code=422, content={"error": {"code": "MIN_TEAMS_TOO_LOW", "message": "minEquipos cannot be less than 3"}})

    @app.exception_handler(EmptyLeaguePasswordError)
    def handle_empty_league_password(request: Request, exc: EmptyLeaguePasswordError):
        return JSONResponse(status_code=422, content={"error": {"code": "EMPTY_LEAGUE_PASSWORD", "message": "A private league requires a non-empty password"}})

    @app.exception_handler(InvalidLeaguePasswordError)
    def handle_invalid_league_password(request: Request, exc: InvalidLeaguePasswordError):
        return JSONResponse(status_code=401, content={"error": {"code": "INVALID_LEAGUE_PASSWORD", "message": "Incorrect league password"}})

    @app.exception_handler(LeagueFullError)
    def handle_league_full(request: Request, exc: LeagueFullError):
        return JSONResponse(status_code=409, content={"error": {"code": "LEAGUE_FULL", "message": "The league is already full"}})

    @app.exception_handler(LeagueAlreadyStartedError)
    def handle_league_already_started(request: Request, exc: LeagueAlreadyStartedError):
        return JSONResponse(status_code=409, content={"error": {"code": "LEAGUE_ALREADY_STARTED", "message": "The league has already started"}})

    @app.exception_handler(AlreadyInLeagueError)
    def handle_already_in_league(request: Request, exc: AlreadyInLeagueError):
        return JSONResponse(status_code=409, content={"error": {"code": "ALREADY_IN_LEAGUE", "message": "Your club is already registered in this league"}})

    @app.exception_handler(LeagueNotFoundError)
    def handle_league_not_found(request: Request, exc: LeagueNotFoundError):
        return JSONResponse(status_code=404, content={"error": {"code": "LEAGUE_NOT_FOUND", "message": "League not found"}})

    @app.exception_handler(MatchDurationNotAllowed)
    def handle_league_not_found(request: Request, exc: LeagueNotFoundError):
        return JSONResponse(status_code=422, content={"error": {"code": "MATCH_DURATION_NOT_ALLOWED", "message": "Match must have a duration of 1, 3 or five minutes."}})

    @app.exception_handler(InvalidFormationError)
    def handle_invalid_formation(request: Request, exc: InvalidFormationError):
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_FORMATION", "message": str(exc)}})

    @app.exception_handler(InsufficientPlayersError)
    def handle_insufficient_players(request: Request, exc: InsufficientPlayersError):
        return JSONResponse(status_code=422, content={"error": {"code": "INSUFFICIENT_PLAYERS", "message": str(exc)}})

    @app.exception_handler(DuplicatePlayersError)
    def handle_duplicate_players(request: Request, exc: DuplicatePlayersError):
        return JSONResponse(status_code=422, content={"error": {"code": "DUPLICATE_PLAYERS", "message": str(exc)}})

    @app.exception_handler(PlayerNotInClubError)
    def handle_player_not_in_club(request: Request, exc: PlayerNotInClubError):
        return JSONResponse(status_code=422, content={"error": {"code": "PLAYER_NOT_IN_CLUB", "message": str(exc)}})

    @app.exception_handler(BehaviorNotAvailableError)
    def handle_behavior_not_available(request: Request, exc: BehaviorNotAvailableError):
        return JSONResponse(status_code=422, content={"error": {"code": "BEHAVIOR_NOT_AVAILABLE", "message": str(exc)}})

    @app.exception_handler(SquadNotConfiguredError)
    def handle_squad_not_configured(request: Request, exc: SquadNotConfiguredError):
        return JSONResponse(status_code=404, content={"error": {"code": "SQUAD_NOT_CONFIGURED", "message": str(exc)}})

    @app.exception_handler(InvalidDurationError)
    def handle_invalid_duration(request: Request, exc: InvalidDurationError):
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_DURATION", "message": str(exc)}})

    @app.exception_handler(SquadRequiredError)
    def handle_squad_required(request: Request, exc: SquadRequiredError):
        return JSONResponse(status_code=422, content={"error": {"code": "SQUAD_NOT_CONFIGURED", "message": str(exc)}})

    @app.exception_handler(FriendlyNotFoundError)
    def handle_friendly_not_found(request: Request, exc: FriendlyNotFoundError):
        return JSONResponse(status_code=404, content={"error": {"code": "MATCH_NOT_FOUND", "message": str(exc)}})

    @app.exception_handler(MatchFullError)
    def handle_match_full(request: Request, exc: MatchFullError):
        return JSONResponse(status_code=409, content={"error": {"code": "MATCH_FULL", "message": str(exc)}})

    @app.exception_handler(MatchNotAvailableError)
    def handle_match_not_available(request: Request, exc: MatchNotAvailableError):
        return JSONResponse(status_code=409, content={"error": {"code": "MATCH_NOT_AVAILABLE", "message": str(exc)}})

    @app.exception_handler(CannotJoinOwnMatchError)
    def handle_cannot_join_own_match(request: Request, exc: CannotJoinOwnMatchError):
        return JSONResponse(status_code=409, content={"error": {"code": "CANNOT_JOIN_OWN_MATCH", "message": str(exc)}})

    @app.exception_handler(NotMatchCreatorError)
    def handle_not_match_creator(request: Request, exc: NotMatchCreatorError):
        return JSONResponse(status_code=403, content={"error": {"code": "NOT_MATCH_CREATOR", "message": str(exc)}})

    @app.exception_handler(MatchNotReadyError)
    def handle_match_not_ready(request: Request, exc: MatchNotReadyError):
        return JSONResponse(status_code=409, content={"error": {"code": "MATCH_NOT_READY", "message": str(exc)}})

    @app.exception_handler(MatchAlreadyStartedError)
    def handle_match_already_started(request: Request, exc: MatchAlreadyStartedError):
        return JSONResponse(status_code=409, content={"error": {"code": "MATCH_ALREADY_STARTED", "message": str(exc)}})
    
    @app.exception_handler(MinTeamsTooLowError)
    def handle_min_teams_too_low(request: Request, exc: MinTeamsTooLowError):
        return JSONResponse(
                status_code=422,
                content={"error": {"code": "MIN_TEAMS_TOO_LOW", "message": "minEquipos cannot be less than 3"}},
                )

    @app.exception_handler(NotInLeagueError)
    def handle_not_in_league(request: Request, exc: NotInLeagueError):
        return JSONResponse(
               status_code=404,
               content={"error": {"code": "NOT_IN_LEAGUE", "message": "Your club is not registered in this league"}},
                )

    @app.exception_handler(AlreadyPlayedMatchesError)
    def handle_already_played_matches(request: Request, exc: AlreadyPlayedMatchesError):
        return JSONResponse(
                status_code=409,
                content={"error": {"code": "ALREADY_PLAYED_MATCHES", "message": "Cannot leave: your club has already played matches in this league"}},
                )

    @app.exception_handler(BehaviorError)
    def handle_behavior_error(request: Request, exc: BehaviorError):
        return JSONResponse(status_code=422, content={"error": {"code": "BEHAVIOR_ERROR", "message": str(exc)}})

    @app.exception_handler(BehaviorInUseError)
    def handle_behavior_in_use(request: Request, exc: BehaviorInUseError):
        return JSONResponse(status_code=409, content={"error": {"code": "BEHAVIOR_IN_USE", "message": "Behavior is already in use in an ongoing match"}})

    @app.exception_handler(MaxTeamsTooLowError)
    def handle_max_teams_too_low(request: Request, exc: MaxTeamsTooLowError):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "MAX_TEAMS_TOO_LOW", "message": "maxEquipos cannot be less than minEquipos"}},
        )
package cmd

import (
	"fmt"
	"log"
	"net/http"
	"shop/pkg/config"
)

func Serve() {
	// godotenv.Load()
	// config.SetConfig()

	// db, err := database.ConnectDB()
	// if err != nil {
	// 	fmt.Println(err.Error())
	// 	return
	// }

	// err = database.AutoMigrate(db)
	// if err != nil {
	// 	fmt.Println(err.Error())
	// 	return
	// }

	// rdb := database.NewRedis(config.LocalConfig.RDBAddress, config.LocalConfig.RDBPassword)
	// err = rdb.Ping(context.Background())
	// if err != nil {
	// 	fmt.Println(err.Error())
	// 	return
	// }

	mux := http.NewServeMux()

	// //repositories
	// userRepo := repositories.NewUserRepository(db, rdb.Client)
	// pollRepo := repositories.NewPollRepository(db, rdb.Client)
	// optionRepo := repositories.NewPollOptionsRepository(db, rdb.Client)
	// voteRepo := repositories.NewCastVoteRepository(db,rdb.Client)

	// //service
	// userService := services.NewUserService(userRepo)
	// pollService := services.NewPollService(pollRepo)
	// optionService := services.NewOptionService(optionRepo)
	// voteService := services.NewCastVoteService(voteRepo)

	// //controller
	// userControllers := controllers.NewUserController(userService)
	// pollControllers := controllers.NewPollControllers(pollService)
	// optionController := controllers.NewOptionController(optionService)
	// voteController   := controllers.NewCastVoteController(voteService)

	// routes.Router(mux, userControllers,pollControllers, optionController, voteController)

	fmt.Println("Server running on port", config.LocalConfig.AppPort)
	log.Fatal(http.ListenAndServe(config.LocalConfig.AppPort,mux ))
}
